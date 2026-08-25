"""抓取 GitHub 热榜数据并生成 data/*.json 快照。

数据来源：
1. github.com/trending 页面（日榜/周榜，无官方 API，HTML 解析）
2. GitHub Search API（近 30 天新建仓库按 star 排序 = "近期涨星最快"的近似）
热点 = 日榜 + 涨最快 合并去重后按 star 排序。

用法：
    GITHUB_TOKEN=xxx python scripts/fetch.py
（不传 token 也能跑，仅 Search API 未认证限流更紧）
"""

import datetime
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from categories import classify  # noqa: E402

DATA_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-trending-site",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
TRENDING_URL = "https://github.com/trending?since={since}"

# 用独立 Session，忽略系统代理（trust_env=False）：本地可能残留 127.0.0.1 代理干扰直连，
# GitHub Actions 环境本身无代理，直连即可。
SESSION = requests.Session()
SESSION.trust_env = False


def get_with_retry(url, headers=None, params=None, timeout=30, retries=3):
    """GET 请求，遇连接类错误自动重试（本地直连/代理可能偶发中断）。"""
    last = None
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            last = e
            if attempt < retries - 1:
                time.sleep(2 * (attempt + 1))
    raise last
SEARCH_URL = "https://api.github.com/search/repositories"
RISING_DAYS = 30
TOP_N = 50


def parse_number(text):
    """把 '1,234' / '12.3k' / '1,234 stars today' 之类的文本转成 int。"""
    s = (text or "").strip().replace(",", "").lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*([km])?", s)
    if not m:
        return 0
    num = float(m.group(1))
    unit = m.group(2)
    if unit == "k":
        num *= 1_000
    elif unit == "m":
        num *= 1_000_000
    return int(num)


def fetch_trending(since):
    """抓取 trending 页（since: daily|weekly），返回 repo 列表。"""
    resp = get_with_retry(TRENDING_URL.format(since=since), headers=UA)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    repos = []
    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        href = h2.get("href", "").strip()
        parts = [p for p in href.split("/") if p]
        if len(parts) < 2:
            continue
        owner, name = parts[0], parts[1]

        desc_el = article.select_one("p")
        description = desc_el.get_text(strip=True) if desc_el else ""

        lang_el = article.select_one('[itemprop="programmingLanguage"]')
        language = lang_el.get_text(strip=True) if lang_el else ""

        stars = forks = 0
        for a in article.select("a"):
            href_a = a.get("href", "")
            text = a.get_text(" ", strip=True)
            if href_a.endswith("/stargazers"):
                stars = parse_number(text)
            elif href_a.endswith("/forks") or "/network/members/" in href_a:
                forks = parse_number(text)

        # 今日/本周涨星：在 float-sm-right 的 span 里（如 "1,234 stars today"）
        stars_gained = 0
        gain_el = article.select_one(".float-sm-right")
        if gain_el:
            stars_gained = parse_number(gain_el.get_text(" ", strip=True))

        # trending 页不展示 topics，改由 API 单独获取（失败则空，分类退化为 language）
        topics = fetch_topics(owner, name)

        repos.append(
            {
                "owner": owner,
                "name": name,
                "url": f"https://github.com/{owner}/{name}",
                "description": description,
                "language": language,
                "stars": stars,
                "starsGained": stars_gained,
                "forks": forks,
                "topics": topics,
            }
        )
    return repos


def fetch_rising():
    """近 30 天新建仓库按 star 排序（近期涨星最快的近似）。"""
    since_date = (
        datetime.date.today() - datetime.timedelta(days=RISING_DAYS)
    ).isoformat()
    params = {
        "q": f"created:>{since_date}",
        "sort": "stars",
        "order": "desc",
        "per_page": TOP_N,
    }
    resp = get_with_retry(SEARCH_URL, params=params, headers=HEADERS)
    resp.raise_for_status()
    repos = []
    for it in resp.json().get("items", []):
        repos.append(
            {
                "owner": it["owner"]["login"],
                "name": it["name"],
                "url": it["html_url"],
                "description": it.get("description") or "",
                "language": it.get("language") or "",
                "stars": it.get("stargazers_count", 0),
                "starsGained": 0,
                "forks": it.get("forks_count", 0),
                "topics": it.get("topics", []),
            }
        )
    return repos


def fetch_topics(owner, name):
    """获取仓库 topics，失败返回空列表（分类会退化为 language 兜底）。"""
    try:
        resp = get_with_retry(
            f"https://api.github.com/repos/{owner}/{name}/topics",
            headers=HEADERS,
            timeout=15,
            retries=2,
        )
        resp.raise_for_status()
        return resp.json().get("names", [])
    except Exception:
        return []


def enrich(repos):
    """给每个 repo 打领域标签。"""
    for r in repos:
        r["category"] = classify(r.get("topics", []), r.get("language", ""))
    return repos


def merge_hot(*lists):
    """合并多份榜单，按 owner/name 去重（保留 star 更高者），按 star 降序。"""
    seen = {}
    for repos in lists:
        for r in repos:
            key = f"{r['owner']}/{r['name']}"
            if key not in seen or r["stars"] > seen[key]["stars"]:
                seen[key] = r
    return sorted(seen.values(), key=lambda r: r["stars"], reverse=True)[:TOP_N]


def write_json(name, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    daily = enrich(fetch_trending("daily"))
    weekly = enrich(fetch_trending("weekly"))
    rising = enrich(fetch_rising())
    hot = merge_hot(daily, rising)

    write_json("trending-daily.json", daily)
    write_json("trending-weekly.json", weekly)
    write_json("rising.json", rising)
    write_json("hot.json", hot)
    write_json(
        "meta.json",
        {
            "updatedAt": datetime.datetime.now(datetime.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
            "risingSinceDays": RISING_DAYS,
            "counts": {
                "daily": len(daily),
                "weekly": len(weekly),
                "rising": len(rising),
                "hot": len(hot),
            },
        },
    )
    print("done:", {k: len(v) for k, v in {
        "daily": daily, "weekly": weekly, "rising": rising, "hot": hot,
    }.items()})


if __name__ == "__main__":
    main()
