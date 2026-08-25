# GitHub 热榜

一个展示 GitHub 热点内容的静态站（[chenzk6.github.io](https://chenzk6.github.io/)）：

- **日榜 / 周榜** —— 抓取 [github.com/trending](https://github.com/trending)
- **涨星最快** —— 近 30 天新建、star 最多的项目（GitHub Search API）
- **热点** —— 日榜 + 涨最快 合并去重

每个项目附带**领域分类标签**（基于 `topics` + `language` 规则映射）和 GitHub 原始描述。

## 工作原理

GitHub Actions 每天定时运行 [scripts/fetch.py](scripts/fetch.py)，抓取数据并生成 `data/*.json` 快照提交回仓库；前端纯静态渲染，无后端、无构建。

## 本地运行

```bash
pip install -r requirements.txt
python scripts/fetch.py      # 生成 data/*.json
python -m http.server        # 浏览器打开 http://localhost:8000
```

## 目录结构

- `index.html` / `style.css` / `app.js` —— 前端页面
- `data/*.json` —— 数据快照（脚本自动生成）
- `scripts/fetch.py` —— 抓取 + 打标签 + 写 JSON
- `scripts/categories.py` —— 领域分类映射规则
- `.github/workflows/update.yml` —— 定时更新（每日 + 手动触发）
