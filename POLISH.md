# MWG 修复 + 视觉美化（mwg-polish）

正文、公式、例题、练习题数值与答案都没改。只改了 `<head>`、内联样式里的颜色 token / hero 写死色、主题切换脚本，并在首页和 explorer 加了主题开关。

## 怎么跑

```
python3 tools/apply_mwg_polish.py           # 给所有页面打补丁（幂等，可重复运行）
python3 tools/apply_mwg_polish.py --check   # 只检查：SRI、meta color-scheme、:root 写死 color-scheme、切换函数是否同步 meta
python3 tools/build_extras.py               # 重新生成 公式速查/易错点/技巧/搜索 页；末尾会自动再跑一次 apply_mwg_polish
python3 tools/verify_tips.py
npx -y modern-web-guidance@latest legacy-scan .
```

`build_extras.py` 会从 `topics/differentiation/index.html` 复制 `<head>`。现在它会先去掉复制来的 `eju-ds.css` 链接，再把这个链接补到本页 extras 样式之后；同时删掉了旧的 `TH-INIT` 头脚本（头脚本已经包含在复制来的 head 里），主题切换改用 `apply_mwg_polish.TOGGLEJS`。脚本末尾 `assert MWG.main() == 0`，所以下次生成不会丢掉 SRI 或 meta。我核对过：补丁之后直接运行 `build_extras.py`，输出与补丁后的状态逐字节相同。

## 一、legacy-scan 修复（改前 50 条：dark-mode-toggle 25、secure-external-subresources 25 → 0）

- **SRI**：所有 KaTeX 0.16.11 的 `<link>` / `<script>`（23 个专题页、claude/）都带上了 `integrity="sha384-…" crossorigin="anonymous" referrerpolicy="no-referrer"`，原有的 `onload` / `onerror` 属性保留。
- **color-scheme**：viewport 之后加 `<meta name="color-scheme" content="light dark">` 和头脚本，与理科三站 build.py 中的 `HEADJS` 相同。原来手写专题页要到 `</body>` 前才设置主题，会先闪一下错误的主题；现在首次绘制前就设置好，并把 meta 改为 light 或 dark。
- **切换函数**：多行版的 `setTheme()`（专题页、claude/）现在同时更新 meta 和 aria-label，并监听 `storage` 事件；压缩版（extras 页）换成共用的 `TOGGLEJS`。
- **CSS**：内联样式里的 `:root { color-scheme: light; … }` / `[data-theme="dark"]` 旧 token 块已删除。token 和 color-scheme 现在统一由 `assets/eju-ds.css` 提供：`:root { color-scheme: light dark }`，`[data-theme=light|dark]` 固定主题，JS 未运行时跟随系统。
- **首页 index.html / explorer/**：原来只用 `prefers-color-scheme`，现在加了与专题页一致的主题开关（同一个 `eju-theme` key）和 meta。从专题页切回首页时主题不会丢。

## 二、视觉

`assets/eju-ds.css` 是四站共用的设计层，与理科三站 `assets/site.css` 末尾的同名块逐字节相同。它链接在每页 `</head>` 前，排在所有内联样式之后：

- Radix slate + indigo 的 12 级思路，浅色和深色两套 token（全部是 6 位 hex），对比度 ≥ 5:1。旧变量名 `--acc/--fg/--card/--mut` 也映射到新 token，所以首页频度表和 explorer 共用同一套色板。原来首页用的 `#2b6cb0` 和专题页用的 `#27508f` 已统一。
- 专题页抬头不再写死深蓝 `#1d2c4d`，跟随主题。
- 按钮、chip、「解答」按钮、卡片、表格、提示框统一圆角、边框和 hover / active；`:focus-visible` 清晰；触控热区约 44px，移动端输入框 ≥ 16px；没有 `transition: all`；reduced-motion 时关掉过渡。
- 顺手修了一个原有 bug：sequences、trig-functions 两页的 `@media print {` 没有闭合，导致其后的 `.back` 等规则只在打印时生效。


## 三、第二轮指定美化（8 点）

这一轮在第一轮之上改动，SRI、meta color-scheme、头脚本、主题切换都保留。第一轮「不新增字体 CDN」和「四站同一个 indigo 主色」两条说明，按这轮要求作废，其余照旧。正文、题目、答案和 demo 计算逻辑都没有改，demo 读取的颜色 token 仍是 6 位 hex。

`tools/apply_mwg_polish.py` 在 `<html>` 上加 `data-site`，在 `<title>` 后插入 `<!--eju-meta-->…<!--/eju-meta-->` 块（favicon、OG / Twitter、`eju-ux.js`），可重复运行；`--check` 会检查这些项与 404.html。`tools/build_extras.py` 末尾仍会自动再跑一次补丁，并且不再写 `tools/__pycache__`。

1. **排版**：中文正文用 Noto Sans SC；日语区域（`:lang(ja)`、`.jp-sub`、`.kana`、术语卡）用 Noto Sans JP。字体在 CSS 里用 `@font-face` 加载，来源是 jsDelivr 上版本锁定的 fontsource woff2（`noto-sans-sc@5.2.5` 的 `chinese-simplified` 与 `latin` 子集、`noto-sans-jp@5.2.5` 的 `japanese` 与 `latin` 子集）。只取 400 和 700，带 `unicode-range`，全部 `font-display: swap`。没有用 Google Fonts 的 `<link>`。标题改为无衬线 700。表格、读数、题号、目录序号都用 `tabular-nums`。正文栏 `--measure: 46rem`，行高 1.7。h2 → 正文约 24px，h3 上 40、下 16，段落间距 12。
2. **间距**：新增 `--s-1 … --s-16` 变量（4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64px），设计层的 margin / padding / gap 都改用它们。
3. **配色**：本站主色是紫（Radix violet），用 `<html data-site="calculus">` 覆盖 `--accent` / `--accent-solid` / `--accent-soft` / `--accent-line` / `--on-accent`。浅色下 accent `#5b47b0`、solid `#6e56cf`；深色下 accent `#baa7ff`、solid `#7d66d9`。深色背景从 `#111113` 改为 `#0f1115`。主色文字在两套主题下对比度都 ≥ 5.1:1。`::selection` 和 `::-moz-selection` 用 `--accent-line` 底配 `--ink` 字。
4. **卡片**：公式卡（`.box`、抬头公式 `.hero-formula`、表格 `.tw`）和例题卡（`.q`，含练习题）统一为墨色 10% 的 1px 边框（`color-mix`，旧浏览器退回 `--line`）、18px 圆角、轻阴影。深色模式下只留 1px 的暗阴影。
5. **微交互**：链接、按钮、chip、目录项、首页卡片都用 150ms 过渡，只过渡 color / background-color / border-color / box-shadow / transform，没有 `transition: all`。按钮和 chip 按下时下沉 1px；滑块按下时变暗。`prefers-reduced-motion: reduce` 下关掉过渡、动画、位移和平滑滚动。
6. **阅读体验**：新增共用脚本 `assets/eju-ux.js`（四站同一份）。① 顶部 3px 主色阅读进度条，按 `<main>` 的滚动进度计算，`pointer-events: none`，只在有目录的专题页出现。② 移动端横向目录在当前小节变化时，自动把高亮项滚入视野。目录本身改为半透明加模糊背景，当前项有底色。③ 点击公式会从 KaTeX 的 `<annotation encoding="application/x-tex">` 取源码并复制，然后弹出「已复制 LaTeX」。正在选取文字、或公式在链接/按钮/summary/demo 里时不复制；复制失败时提示改为手动选取，不会抛未捕获错误。公式的 DOM 和 MathML 都不改。
7. **细节**：`assets/favicon.svg`、`favicon-32.png`、`apple-touch-icon.png` 用本站主色；所有页面 head 都链接了它们。OG 图 `assets/og.png` 是 1200×630 的 PNG，`og:image` 为 `https://feather0000.github.io/eju-calculus/assets/og.png`，另有 og:title / og:description / og:url 和 `twitter:card=summary_large_image`。根目录新增 `404.html`，带头脚本、主题开关和回首页链接，资源用 `/eju-calculus/…` 绝对路径。
8. **性能**：字体全部 `font-display: swap`。仓库里没有 `<img>`，也没有为了转 WebP 去动 canvas。OG 图为兼容各平台保留 PNG，canvas 也不做懒加载。apply_mwg_polish.py 会给以后出现的 `<img>` 自动补 `loading="lazy"`。

favicon 和 OG 图由 `/workspace/eju-polish-work/scripts/make_brand.py`（Pillow）生成，四站用同一套版式。设计层和 `eju-ux.js` 的母版在 `/workspace/eju-polish-work/`，用 `scripts/sync_ds.py` 同步到四站。

## 四、统一视觉、合并重复讲义、顶栏与搜索修复（fix-design-nav-search）

正文、公式、例题、练习题数值与答案都没改。

1. **统一视觉**：新增 `assets/paper.css`（只有数学站有），由 `apply_mwg_polish.ds_link()` 紧跟在 `eju-ds.css` 之后链接到专题页、`claude/`、`explorer/` 和 404。它把中性色换成首页目次同一套纸色（值与 `home.css` 的 `body.contents` 相同，卡片面 `--surface` 略亮一档），并让 `h1`、`main h2` 用首页的衬线 700。主色不变，token 仍是 6 位 hex。`eju-ds.css` 本身没有改，仍与理科三站逐字节相同。`--check` 会检查 `paper.css` 是否已链接。
2. **重复讲义**：`codex/` 与 `claude/` 覆盖同一范围，且是全站唯一一套绿色设计。`codex/` 目录已整个删除（旧的 `codex/` 链接会落到 404 页），首页「附」里的入口从 `tools/build_home.py` 去掉，`apply_mwg_polish.py` 不再处理它。原页面在 git 历史里（`a0694e7` 及之前）。
3. **顶栏**：微分、积分、三角函数和四个速查页的内联样式里有不带范围的 `details > summary` 按钮样式，把顶栏的「全部专题」也画成了带边框的大按钮。`assets/nav.js` 注入的样式里加了一条重置。
4. **搜索**：摘要截取时不再把 `$…$` 公式切成两半，结果写入后交给 KaTeX 渲染（索引在 900 字处截断留下的半个公式不显示）；术语标题的中文与日语之间加「／」；标题外包一层 `<span>`，避免 `inline-flex` 吃掉空格；搜索页抬头不再输出空的公式卡片。

**注意**：`assets/search.js` 和速查页的内联样式由 `tools/build_extras.py` 从仓库外的 `/workspace/eju-common/` 复制。这次直接改了仓库里的 `assets/search.js`、`assets/search.json`（1119 条术语标题）和 `topics/search/index.html`；`build_extras.py` 里术语分隔、空公式卡片、`paper.css` 链接三处已同步，但 `/workspace/eju-common/search.js` 需要手动同步，否则下次运行会把搜索的修改盖回去。
