# 数学站：给所有页面补 MWG 修复与共用设计层（可重复运行，幂等）
#   python3 tools/apply_mwg_polish.py          # 处理全部页面
#   python3 tools/apply_mwg_polish.py --check  # 只检查，不写文件；有缺项时退出码 1
# 做的事：
#   1. KaTeX 0.16.11 的 <link>/<script> 加 integrity（sha384）+ crossorigin="anonymous" + referrerpolicy="no-referrer"
#   2. <head> 尽早加 <meta name="color-scheme" content="light dark"> 与头脚本（首次绘制前按 localStorage['eju-theme']
#      或 prefers-color-scheme 设 data-theme，并把 meta 改成 light / dark）
#   3. 内联样式去掉写死的 color-scheme: light 与旧色板 token、hero 的写死深蓝；在 </head> 前链接 assets/eju-ds.css
#   4. 主题切换函数同步更新 data-theme、meta color-scheme、按钮文案与 aria-label、localStorage（并响应其它标签页）
#   5. 首页 index.html 与 explorer/ 加上同一个主题开关（同一个 localStorage key：eju-theme）；首页由 tools/build_home.py 生成时（带 HOME_MARK）不改结构
#   6. （第二轮）<html data-site="calculus">（每站主色 violet，见 eju-ds.css）；favicon；OG / Twitter 分享卡片（og:image 绝对 URL）；
#      专题页、claude/、explorer/ 加共用交互脚本 assets/eju-ux.js（阅读进度条、横向目录跟随、点击公式复制 LaTeX）
#   7. （第二轮）根目录 404.html（GitHub Pages 用；资源走站点绝对路径）
import re, glob, os, sys, html
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
K = 'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/'
SRI = {'katex.min.css': 'sha384-nB0miv6/jRmo5UMMR1wu3Gz6NLsoTkbqJghGIsx//Rlm+ZU03BU6SQNC66uf4l5+',
       'katex.min.js': 'sha384-7zkQWkzuo3B5mTepMUcHkMB5jZaolc2xDwL6VFqjFALcbeS9Ggm/Yr2r3Dy4lfFg',
       'contrib/auto-render.min.js': 'sha384-43gviWU0YVjaDtb/GhzOouOXtZMP/7XUzwPTstBeZFe/+rCMvRwr4yROQP43s0Xk',
       'contrib/mhchem.min.js': 'sha384-ifpG+NlgMq0kvOSGqGQxW1mJKpjjMDmZdpKGq3tbvD3WPhyshCEEYClriK/wRVU0'}
# 与理科三站 build.py 中 HEADJS / TOGGLEJS 相同
HEADJS = """<script>(function(){var d=document.documentElement,m=document.querySelector('meta[name="color-scheme"]'),t=null;try{t=localStorage.getItem('eju-theme')}catch(e){}if(t!=='light'&&t!=='dark')t=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';d.setAttribute('data-theme',t);if(m)m.content=t})()</script>"""
TOGGLEJS = """<script>(function(){var d=document.documentElement,b=document.getElementById('theme');if(!b)return;function s(t){d.setAttribute('data-theme',t);var m=document.querySelector('meta[name="color-scheme"]');if(m)m.content=t;b.textContent=t==='dark'?'浅色':'深色';b.setAttribute('aria-label',t==='dark'?'切换到浅色主题':'切换到深色主题')}s(d.getAttribute('data-theme')==='dark'?'dark':'light');b.onclick=function(){var t=d.getAttribute('data-theme')==='dark'?'light':'dark';s(t);try{localStorage.setItem('eju-theme',t)}catch(e){}};addEventListener('storage',function(e){if(e.key==='eju-theme'&&(e.newValue==='light'||e.newValue==='dark'))s(e.newValue)});var q=window.matchMedia&&matchMedia('(prefers-color-scheme: dark)');if(q&&q.addEventListener)q.addEventListener('change',function(e){var v=null;try{v=localStorage.getItem('eju-theme')}catch(_){}if(v!=='light'&&v!=='dark')s(e.matches?'dark':'light')})})();</script>"""
BTN = '<button class="chip theme-btn" id="theme" type="button">深色</button>'
SITE = 'calculus'; SITE_NAME = 'EJU 数学コース2'; SITE_PATH = '/'; SITE_URL = 'https://math.eju.feather0.com/'
SITE_DESC = '按 JASSO《日本留学試験 数学シラバス》（2026 年度第 1 回起适用）出题项目 1–20 编排。每页含要点讲解、原创 EJU 风格例题、带答案的练习题和日语术语对照表。'
META_RE = re.compile(r'<!--eju-meta-->.*?<!--/eju-meta-->\n?', re.S)


def sri(s):
    def fix(m):
        tag, f = m.group(0), m.group(2)
        if f not in SRI: return tag
        tag = re.sub(r'\s+(integrity="[^"]*"|crossorigin(="[^"]*")?|referrerpolicy="[^"]*")', '', tag)
        return tag[:-1] + f' integrity="{SRI[f]}" crossorigin="anonymous" referrerpolicy="no-referrer">'
    return re.sub(r'<(link|script)\b[^>]*?(?:href|src)="' + re.escape(K) + r'([^"?#]+)"[^>]*>', fix, s)


def head_meta(s, scheme='light dark', script=True):
    s = re.sub(r'<meta name="color-scheme"[^>]*>\n?', '', s)
    s = re.sub(r'<script>\(function\(\)\{var d=document\.documentElement,m=document\.querySelector\(\'meta\[name="color-scheme"\]\'\).*?</script>\n?', '', s, count=1, flags=re.S)
    s = re.sub(r'<script>/\*TH-INIT\*/.*?</script>', '', s, flags=re.S)
    ins = f'<meta name="color-scheme" content="{scheme}">' + ('\n' + HEADJS if script else '')
    m = re.search(r'<meta name="viewport"[^>]*>', s) or re.search(r'<meta charset[^>]*>', s)
    return s[:m.end()] + ins + '\n' + s[m.end():]


def ds_link(s, root):
    # 数学站另有纸色层 assets/paper.css（与首页目次同一套纸色、衬线标题），紧跟在设计层之后
    s = re.sub(r'<link rel="stylesheet" href="[./]*assets/(?:eju-ds|paper)\.css">\n?', '', s)
    return s.replace('</head>', f'<link rel="stylesheet" href="{root}assets/eju-ds.css">\n<link rel="stylesheet" href="{root}assets/paper.css">\n</head>', 1)


def inline_css(s):
    """专题页内联样式：去掉旧 token 块（含 color-scheme: light）与 hero 写死色。"""
    s = re.sub(r':root \{\n  color-scheme: light;\n.*?\n\}\n\[data-theme="dark"\] \{\n  color-scheme: dark;\n.*?\n\}\n',
               '/* 颜色 token、明暗主题与 color-scheme 见 assets/eju-ds.css */\n', s, count=1, flags=re.S)
    for a, b in [('html { scroll-behavior: smooth; ', 'html { '),
                 ('.hero { background: #1d2c4d; color: #f4f1e8;', '.hero { background: var(--hero-bg); color: var(--hero-ink);'),
                 ('color: #c5d3ef; margin: 0 0 12px;', 'color: var(--accent); margin: 0 0 12px;'),
                 ('color: #dfe4ee;', 'color: var(--hero-ink-2);'),
                 ('border-left: 2px solid #5f78aa;', 'border-left: 1px solid var(--hero-line);'),
                 ('.back { display: inline-block; color: #c5d3ef;', '.back { display: inline-block; color: var(--hero-ink-2);'),
                 ('.hero .back a { color: #c5d3ef;', '.hero .back a { color: var(--hero-ink-2);')]:
        s = s.replace(a, b)
    # 原有 bug（sequences、trig-functions）：@media print { 未闭合，其后的 .back 等规则只在打印时生效
    s = s.replace('  .ans[hidden] { display: block; }\n.back {', '  .ans[hidden] { display: block; }\n}\n.back {')
    # 其余变体（如 .back a { color: #c5d3ef; }）：抬头里写死的浅蓝字一律改为跟随主题
    i = s.find('</head>')
    return s[:i].replace('#c5d3ef', 'var(--hero-ink-2)') + s[i:]


def toggle(s):
    # 多行版（手写专题页、claude/）
    s = re.sub(r"(function setTheme\(t\) \{\n(\s*)document\.documentElement\.setAttribute\('data-theme', t\);\n)(?!\s*var m = document\.querySelector)",
               lambda m: m.group(1) + m.group(2) + "var m = document.querySelector('meta[name=\"color-scheme\"]'); if (m) m.content = t;\n"
               + m.group(2) + "themeBtn.setAttribute('aria-label', t === 'dark' ? '切换到浅色主题' : '切换到深色主题');\n", s)
    s = re.sub(r"setTheme\(store\(\) \|\| \(window\.matchMedia && matchMedia\('\(prefers-color-scheme: dark\)'\)\.matches \? 'dark' : 'light'\)\);",
               "setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');\n"
               "  addEventListener('storage', function (e) { if (e.key === 'eju-theme' && (e.newValue === 'light' || e.newValue === 'dark')) setTheme(e.newValue); });", s)
    # 压缩版（build_extras 生成的速查/易错/技巧/搜索页）
    s = s.replace("<script>(function(){var b=document.getElementById('theme');function s(t){document.documentElement.setAttribute('data-theme',t);b.textContent=t==='dark'?'浅色':'深色'}s(document.documentElement.getAttribute('data-theme')||'light');b.onclick=function(){var t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';s(t);try{localStorage.setItem('eju-theme',t)}catch(e){}};\n",
                  TOGGLEJS + "<script>(function(){\n")
    return s


def add_toggle(s):
    """没有主题开关的页面（首页、explorer）：在 nav.js / </body> 前放 TOGGLEJS。"""
    s = s.replace(TOGGLEJS, '')
    m = re.search(r'<script src="[./]*assets/nav\.js"></script>', s)
    i = m.start() if m else s.rindex('</body>')
    return s[:i] + TOGGLEJS + s[i:]


def site_attr(s):
    return re.sub(r'<html\b([^>]*)>', lambda m: '<html' + re.sub(r'\s+data-site="[^"]*"', '', m.group(1)) + f' data-site="{SITE}">', s, count=1)


def headmeta(s, root, path, ux=True):
    """<title> 之后插入 favicon、OG / Twitter 卡片（与理科三站 build.py 的 headmeta 相同）与 eju-ux.js；用注释标记，重复运行先删后加。"""
    s = META_RE.sub('', s)
    title = html.unescape(re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip())
    m = re.search(r'<meta name="description" content="([^"]*)"', s)
    desc = html.unescape(m.group(1)) if m else SITE_DESC
    t, d = html.escape(title), html.escape(desc)
    blk = ('<!--eju-meta-->' + ('' if m else f'<meta name="description" content="{d}">')
           + f'<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="{root}assets/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">\n'
           + f'<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:locale" content="zh_CN"><meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{SITE_URL}{path}">'
           + f'<meta property="og:image" content="{SITE_URL}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{SITE_NAME} · 全专题中文讲义">'
           + f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{t}"><meta name="twitter:description" content="{d}"><meta name="twitter:image" content="{SITE_URL}assets/og.png">'
           + (f'\n<script defer src="{root}assets/eju-ux.js"></script>' if ux else '') + '<!--/eju-meta-->\n')
    i = s.index('</title>') + len('</title>')
    if s[i:i + 1] == '\n': i += 1
    return s[:i] + blk + s[i:]


def brand(s, root, path, ux=True):
    return headmeta(site_attr(s), root, path, ux)


NOT_FOUND = f'''<!doctype html><html lang="zh-Hans" data-site="{SITE}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light dark">
{HEADJS}<title>页面不存在 · {SITE_NAME}</title><meta name="robots" content="noindex"><link rel="icon" href="{SITE_PATH}assets/favicon.svg" type="image/svg+xml"><link rel="icon" href="{SITE_PATH}assets/favicon-32.png" sizes="32x32" type="image/png"><link rel="apple-touch-icon" href="{SITE_PATH}assets/apple-touch-icon.png">
<link rel="stylesheet" href="{SITE_PATH}assets/eju-ds.css"><link rel="stylesheet" href="{SITE_PATH}assets/paper.css"></head><body class="home nf"><main>
<div class="home-top"><p class="eyebrow">{SITE_NAME}</p>{BTN}</div>
<p class="nf-code" aria-hidden="true">404</p><h1>页面不存在</h1><p>这个地址没有对应的页面：可能是链接写错了，或者页面已经移动。可以回到首页按专题查找，或用站内搜索。</p>
<p class="home-links"><a href="{SITE_PATH}">← 回到 {SITE_NAME} 首页</a><a href="{SITE_PATH}topics/search/">站内搜索</a></p></main>
{TOGGLEJS}</body></html>
'''


def lazy_img(s):
    """<img> 一律 loading="lazy"（目前页面里没有 img；以后加图时自动补上）"""
    return re.sub(r'<img\b(?![^>]*\bloading=)', '<img loading="lazy"', s)


def topic(s, root, path):
    return lazy_img(brand(ds_link(toggle(inline_css(head_meta(sri(s)))), root), root, path))


HOME_MARK = '<!--home: tools/build_home.py-->'


def home(s):
    if HOME_MARK in s:  # tools/build_home.py 生成的目次首页：结构与样式顺序（eju-ds.css 之后是 home.css）已定，只做幂等的头部补丁
        return lazy_img(brand(add_toggle(head_meta(sri(s))), '', '', ux=False))
    s = head_meta(sri(s))
    # 去掉旧的首页色板 + 基础样式（由 eju-ds.css 的 .home 规则接管）；mathfreq 等其余样式保留
    s = re.sub(r'<style>:root\{--bg:#fafaf7;.*?</style>', '', s, count=1, flags=re.S)
    s = s.replace('<body><main>', '<body class="home"><main>', 1)
    if 'id="theme"' not in s:
        s = s.replace('<main>\n<h1>', f'<main>\n<div class="home-top"><p class="eyebrow">EJU 数学 · コース2</p>{BTN}</div>\n<h1>', 1)
    return lazy_img(brand(add_toggle(ds_link(s, '')), '', '', ux=False))


def explorer(s):
    s = head_meta(sri(s))
    s = re.sub(r':root\{--bg:#fafaf7;[^}]*\}@media\(prefers-color-scheme:dark\)\{:root\{[^}]*\}\}', '', s, count=1)
    if 'id="theme"' not in s:
        s = s.replace('<main><p><a href="../">← 目录</a></p>', f'<main><p class="topbar"><a href="../">← 目录</a>{BTN}</p>', 1)
    return lazy_img(brand(add_toggle(ds_link(s, '../')), '../', 'explorer/'))


def problems(f, s):
    p = []
    for m in re.finditer(r'<(link|script)\b[^>]*katex@[^>]*>', s):
        t = m.group(0)
        if 'integrity="sha384-' not in t or 'crossorigin="anonymous"' not in t or 'referrerpolicy="no-referrer"' not in t: p.append('SRI ' + t[:80])
    if '<meta name="color-scheme"' not in s: p.append('no meta color-scheme')
    if re.search(r':root\s*\{\s*color-scheme:\s*light\s*;', s): p.append(':root color-scheme: light')
    if "setAttribute('data-theme'" in s.replace(HEADJS, '') and 'eju-theme' in s and 'm.content = t' not in s and 'm.content=t' not in s.replace(HEADJS, ''):
        p.append('theme toggle does not update meta')
    if f'data-site="{SITE}"' not in s[:300]: p.append('no data-site')
    if 'assets/favicon.svg' not in s: p.append('no favicon')
    if f'property="og:image" content="{SITE_URL}assets/og.png"' not in s or 'name="twitter:card"' not in s: p.append('no og/twitter card')
    if re.search(r'<img\b(?![^>]*\bloading=)', s): p.append('img without loading')
    if f.startswith(('topics/', 'claude/', 'explorer/')) and 'assets/eju-ux.js' not in s: p.append('no eju-ux.js')
    if f.startswith(('topics/', 'claude/', 'explorer/')) and 'assets/paper.css' not in s: p.append('no paper.css')
    return p


def targets():
    os.chdir(ROOT)
    out = [(f, (lambda s, r='../../', p=f[:-len('index.html')]: topic(s, r, p))) for f in sorted(path.replace(os.sep, '/') for path in glob.glob('topics/*/index.html'))]
    out += [('claude/index.html', lambda s: topic(s, '../', 'claude/')), ('index.html', home), ('explorer/index.html', explorer)]
    return [(f, fn) for f, fn in out if os.path.exists(f)]


def main(check=False, files=None):
    bad = 0
    for f, fn in targets():
        if files and f not in files: continue
        s0 = open(f).read(); s = s0 if check else fn(s0)
        if not check and s != s0: open(f, 'w').write(s)
        p = problems(f, s)
        if p: bad += 1; print('FAIL', f, p)
    if not files:
        nf = open('404.html').read() if os.path.exists('404.html') else ''
        if nf != NOT_FOUND:
            if check: bad += 1; print('FAIL 404.html out of date')
            else: open('404.html', 'w').write(NOT_FOUND)
    print(('checked' if check else 'patched'), len(targets()), 'pages,', bad, 'with problems')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main(check='--check' in sys.argv) else 0)
