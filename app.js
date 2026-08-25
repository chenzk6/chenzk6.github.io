'use strict';

const TABS = [
  { id: 'daily',  label: '日榜',     file: 'data/trending-daily.json',  gain: '今日', rising: false },
  { id: 'weekly', label: '周榜',     file: 'data/trending-weekly.json', gain: '本周', rising: false },
  { id: 'rising', label: '涨星最快', file: 'data/rising.json',          gain: null,   rising: true  },
  { id: 'hot',    label: '热点',     file: 'data/hot.json',             gain: null,   rising: false },
];

// 与 scripts/categories.py 中的领域保持一致的配色
const COLORS = {
  'AI/ML': '#7c3aed', '前端': '#2563eb', '后端': '#059669', 'DevOps': '#ea580c',
  '安全': '#dc2626', '数据': '#0891b2', '移动端': '#db2777', '桌面': '#4f46e5',
  '游戏': '#9333ea', '工具': '#64748b', '其他': '#9ca3af',
};

const state = { tab: 'daily', category: '', language: '', query: '' };
const cache = {};
const el = (id) => document.getElementById(id);

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function fmt(n) {
  if (n == null || isNaN(n)) return '0';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(1) + 'k';
  return String(n);
}

function categoryColor(name) { return COLORS[name] || COLORS['其他']; }

async function load() {
  const files = [...new Set(TABS.map((t) => t.file))];
  await Promise.all(files.map(async (f) => {
    if (cache[f]) return;
    const r = await fetch(f);
    if (!r.ok) throw new Error('无法加载 ' + f);
    cache[f] = await r.json();
  }));
  try {
    const m = await fetch('data/meta.json');
    if (m.ok) {
      const meta = await m.json();
      el('updated').textContent = '最后更新：' + new Date(meta.updatedAt).toLocaleString('zh-CN');
    }
  } catch (_) { /* 忽略 meta 加载失败 */ }
}

function allRepos() {
  return TABS.flatMap((t) => cache[t.file] || []);
}

function currentRepos() {
  return cache[TABS.find((t) => t.id === state.tab).file] || [];
}

function renderTabs() {
  el('tabs').innerHTML = TABS.map((t) =>
    `<button class="tab${t.id === state.tab ? ' active' : ''}" data-tab="${t.id}">${t.label}</button>`
  ).join('');
}

function renderChips() {
  const cats = [...new Set(allRepos().map((r) => r.category).filter(Boolean))].sort();
  const all = `<button class="chip${state.category === '' ? ' active' : ''}" data-cat="">全部</button>`;
  const rest = cats.map((c) =>
    `<button class="chip${c === state.category ? ' active' : ''}" data-cat="${esc(c)}">
      <span class="dot" style="background:${categoryColor(c)}"></span>${esc(c)}</button>`
  ).join('');
  el('chips').innerHTML = all + rest;
}

function renderLanguages() {
  const langs = [...new Set(currentRepos().map((r) => r.language).filter(Boolean))].sort();
  el('language').innerHTML =
    '<option value="">全部语言</option>' +
    langs.map((l) => `<option value="${esc(l)}"${l === state.language ? ' selected' : ''}>${esc(l)}</option>`).join('');
}

function render() {
  const tab = TABS.find((t) => t.id === state.tab);
  let repos = currentRepos();
  if (state.category) repos = repos.filter((r) => r.category === state.category);
  if (state.language) repos = repos.filter((r) => r.language === state.language);
  if (state.query) {
    const q = state.query.toLowerCase();
    repos = repos.filter((r) =>
      (r.name + ' ' + (r.owner || '') + ' ' + (r.description || '')).toLowerCase().includes(q));
  }

  const cards = repos.map((r, i) => {
    const gain = (tab.gain && r.starsGained)
      ? `<span class="gain">▲ ${fmt(r.starsGained)} ${tab.gain}</span>` : '';
    const rising = tab.rising ? '<span class="rising-badge">近30天新建</span>' : '';
    const lang = r.language ? `<span class="lang">${esc(r.language)}</span>` : '';
    const desc = r.description
      ? `<p class="desc">${esc(r.description)}</p>`
      : '<p class="desc empty">暂无描述</p>';
    const color = categoryColor(r.category);
    return `
      <article class="card">
        <div class="rank">${i + 1}</div>
        <div class="body">
          <div class="row1">
            <a class="name" href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.owner)}/<strong>${esc(r.name)}</strong></a>
            <span class="badge" style="background:${color}22;color:${color}">${esc(r.category)}</span>
          </div>
          ${desc}
          <div class="row2">
            ${gain}${rising}
            <span class="stat">★ ${fmt(r.stars)}</span>
            <span class="stat">⑂ ${fmt(r.forks)}</span>
            ${lang}
          </div>
        </div>
      </article>`;
  }).join('');

  el('list').innerHTML = repos.length ? cards : '<p class="empty-list">没有匹配的项目</p>';
}

function renderAll() {
  renderTabs();
  renderChips();
  renderLanguages();
  render();
}

function bind() {
  el('tabs').addEventListener('click', (e) => {
    const b = e.target.closest('.tab');
    if (!b) return;
    state.tab = b.dataset.tab;
    state.language = '';
    state.category = '';
    state.query = '';
    el('search').value = '';
    renderAll();
  });
  el('chips').addEventListener('click', (e) => {
    const b = e.target.closest('.chip');
    if (!b) return;
    state.category = b.dataset.cat;
    renderChips();
    render();
  });
  el('language').addEventListener('change', (e) => {
    state.language = e.target.value;
    render();
  });
  el('search').addEventListener('input', (e) => {
    state.query = e.target.value.trim();
    render();
  });
}

(async () => {
  bind();
  try {
    await load();
    renderAll();
  } catch (err) {
    el('list').innerHTML = `<p class="empty-list">数据加载失败：${esc(err.message)}</p>`;
  }
})();
