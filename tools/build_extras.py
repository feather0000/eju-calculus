# 数学站：生成 公式速查 / 易错点 / 站内搜索 页面与 assets/search.json；更新 nav.js；重新生成首页（tools/build_home.py）
import re, glob, os, json, html as H, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.dont_write_bytecode = True  # 不在 tools/ 留 __pycache__
sys.path.insert(0, 'tools')
from _x import formula_sections, pitfall_sections, search_sections, plain, CATS, tips_sections, tip_backsec, detex
from math_tips import TIPS
from math_data import F, PF
import apply_mwg_polish as MWG  # SRI / meta color-scheme / 头脚本 / 主题切换 / eju-ds.css
EX = ['formulas', 'pitfalls', 'search', 'tips']
# —— 读取现有专题页 ——
TOP = []
for f in sorted(glob.glob('topics/*/index.html')):
    slug = os.path.basename(os.path.dirname(f))
    if slug in EX: continue
    s = open(f).read()
    n = re.search(r'"n": (\d+), "slug": "%s"' % slug, open('assets/nav.js').read().split('\n')[0])
    secs = [(a, re.sub('<[^>]+>', '', b), '', '') for a, b in re.findall(r'<section id="([^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>', s)]
    TOP.append(dict(slug=slug, n=int(n.group(1)) if n else 0, zh=re.sub('<[^>]+>', '', re.search(r'<h1>(.*?)</h1>', s).group(1)).strip(),
                    ja=re.sub('<[^>]+>', '', re.search(r'class="eyebrow">(.*?)</p>', s).group(1)).split('·')[-1].strip(), sections=secs, problems=[], terms=[], src=s))
TOP.sort(key=lambda t: t['n'])
# 去掉标题前的编号（如“15 复数平面”）
for t in TOP: t['zh'] = re.sub(r'^\d+\s+', '', t['zh'])
src = open('topics/differentiation/index.html').read()
HEAD = src[:src.index('</head>')]
# 设计层链接要排在本页 extras 样式之后，先从复制来的 head 里拿掉，下面再补到 </head> 前
HEAD = re.sub(r'<link rel="stylesheet" href="\.\./\.\./assets/(?:eju-ds|paper)\.css">\n?', '', HEAD)
XCSS = open('tools/extras.css').read()
def page(slug, n, zh, ja, lead, hero, sections, desc):
    head = re.sub(r'<title>.*?</title>', f'<title>EJU 数学コース2 · {zh}</title>', HEAD, count=1)
    head = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{H.escape(desc)}">', head, count=1)
    head = head.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">')
    toc = ''.join(f'<li><a href="#{i}">{k+1} {tt}</a></li>' for k, (i, tt, _, _) in enumerate(sections))
    secs = ''.join(f'<section id="{sid}"><h2>{tt}</h2><p class="jp-sub">{j}</p>{body}</section>' for sid, tt, j, body in sections)
    hero = ''.join(f'$${h}$$' for h in hero)
    hero = f'<div class="hero-formula" aria-hidden="true">{hero}</div>' if hero else ''  # 搜索页没有代表式，不留空卡片
    return f'''{head}<style id="extras">{XCSS}</style>
<link rel="stylesheet" href="../../assets/eju-ds.css">
<link rel="stylesheet" href="../../assets/paper.css">
</head>
<body>
<a class="skip" href="#main">跳到正文</a>
<div id="cdn-note" hidden>公式库（KaTeX）未能加载，公式将显示为源码。请联网后刷新页面。</div>
<header class="hero"><div class="hero-in"><div class="hero-text"><a class="back" href="../../">← 目录</a><p class="eyebrow">EJU 数学コース2 · 速查 · {ja}</p><h1>{zh}</h1><p class="lead">{lead}</p></div>{hero}</div></header>
<div class="layout"><nav class="toc" aria-label="目录"><div style="flex:1;min-width:0"><p class="toc-title">目录</p><ol>{toc}</ol></div><button class="chip theme-btn" id="theme" type="button">深色</button></nav>
<main id="main">{secs}<footer>原创讲义，非 JASSO 官方内容。按《日本留学試験 数学シラバス（コース2）》编排。</footer></main></div>
{MWG.TOGGLEJS}<script>(function(){{
var L=[].slice.call(document.querySelectorAll('nav.toc a'));if('IntersectionObserver'in window){{var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting)L.forEach(function(a){{a.classList.toggle('on',a.getAttribute('href')==='#'+e.target.id)}})}})}},{{rootMargin:'-20% 0px -70% 0px'}});document.querySelectorAll('main section').forEach(function(x){{io.observe(x)}})}}
window.addEventListener('load',function(){{if(!window.renderMathInElement){{document.getElementById('cdn-note').hidden=false;return}}renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],macros:{{'\\\\B':'\\\\boxed{{\\\\text{{#1}}}}'}},throwOnError:false}})}})}})();</script>
<script src="../../assets/nav.js"></script>
</body>
</html>
'''
FS = formula_sections(TOP, F)
PS = pitfall_sections(TOP, PF)
SS = search_sections()
_A = json.load(open('assets/bank_analysis.json')); _w = {}
for e in _A['entries']:
    for k, v in e['topics'].items(): _w[k] = _w.get(k, 0) + v
WT = {k: (v, f'过去问加权 {v:.1f} 题') for k, v in _w.items()}
TS = tips_sections(TOP, TIPS, WT)
# —— 专题页反向链接（幂等） ——
for t in TOP:
    f = f'topics/{t["slug"]}/index.html'; s0 = re.sub(r'<!--TIPS-BEGIN-->.*?<!--TIPS-END-->', '', open(f).read(), flags=re.S)
    b = tip_backsec(t['slug'], TIPS)
    if b:
        blk = f'<!--TIPS-BEGIN--><section id="tips"><h2>快速解题技巧</h2><p class="jp-sub">速解テクニック</p>{b[3]}</section><!--TIPS-END-->'
        assert s0.count('<footer') == 1, f; s0 = s0.replace('<footer', blk + '<footer', 1)
        if '.tip-back' not in s0: s0 = s0.replace('</head>', '<style>.tip-back{padding-left:1.2em}.tip-back li{margin:4px 0}.tip-back a{display:inline-block;min-height:28px}</style></head>', 1)
    open(f, 'w').write(s0); t['src'] = s0
PAGES = [('formulas', 21, '公式速查', '公式集', '各专题最常用的公式，和“什么时候能用”的条件放在一起。点每组下面的链接回到对应讲解与练习。', [r'\frac{a}{\sin A}=2R', r'\int_\alpha^\beta(x-\alpha)(x-\beta)dx=-\tfrac{(\beta-\alpha)^3}{6}'], FS, '按专题的核心公式与成立条件'),
         ('pitfalls', 22, '易错点・陷阱', '間違えやすいポイント', '按错误类型整理：成立条件（真数条件、区间、收敛、等号）、符号与方向、概念混淆、读题。每条有简短例子，并链接到相关讲解与练习。', [r'\sqrt{a^2}=|a|', r'a_n=S_n-S_{n-1}\ (n\ge2)'], PS, f'{len(PF)} 个常见错误与例子'),
         ('tips', 24, '快速解题技巧', '速解テクニック', 'EJU 数学コース2 是マーク式（空格填数字）。这里整理能直接省时间、也能用来验算的方法：空格形状检查、顶点式、韦达、根的分布、切线、1/6 公式、向量系数比较、余事象……专题按过去问加权出题频度排序。', [r'\tfrac{|a|}{6}(\beta-\alpha)^3', r'\alpha^2+\beta^2=(\alpha+\beta)^2-2\alpha\beta'], TS, f'{len(TIPS)} 招 · 按出题频度排序'),
         ('search', 23, '站内搜索', 'サイト内検索', '搜索本站的讲解、练习、公式、易错点和日语术语。中文和日语都可以搜（会自动对应常见的日本汉字写法）。', [], SS, '讲解・练习・公式・术语')]
for slug, n, zh, ja, lead, hero, secs, sub in PAGES:
    os.makedirs(f'topics/{slug}', exist_ok=True)
    open(f'topics/{slug}/index.html', 'w').write(page(slug, n, zh, ja, lead, hero, secs, zh + '：' + sub))
# —— 搜索索引 ——
I = []
TERM = re.compile(r"\[\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\s*\]")
for t in TOP:
    s = t['src']; u = f'topics/{t["slug"]}/'
    lead = re.search(r'class="lead">(.*?)</p>', s, re.S)
    I.append(['页', f'{t["n"]} {t["zh"]}', plain(t['ja'] + ' ' + (lead.group(1) if lead else '')), u])
    parts = re.split(r'(?=<section id=")', s)
    for p in parts:
        m = re.match(r'<section id="([^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>', p)
        if not m: continue
        sid, tt = m.group(1), plain(m.group(2))
        body = p[:p.find('</section>')] if '</section>' in p else p
        if sid == 'terms':
            m2 = re.search(r'var TERMS = \[(.*?)\n  \];', s, re.S)
            rows = TERM.findall(m2.group(1)) if m2 else []
            rows += re.findall(r'<tr><td lang="ja">(.*?)</td><td class="kana" lang="ja">(.*?)</td><td>(.*?)</td></tr>', body)
            for ja, kana, zh in rows: I.append(['术语', plain(zh) + ' ／ ' + plain(ja), plain(f'{kana} · {t["zh"]}'), u + '#terms'])
            continue
        arts = re.findall(r'<article class="q"[^>]*>(.*?)</article>', body, re.S)
        if arts:
            for a in arts:
                hd = re.search(r'<div class="q-head"><b>(.*?)</b>', a)
                I.append(['题', f'{t["zh"]} · {plain(hd.group(1)) if hd else tt}', plain(re.sub(r'<div class="q-head">.*?</div>', '', a, count=1, flags=re.S))[:500], u + '#' + sid])
            body = re.sub(r'<article class="q".*?</article>', '', body, flags=re.S)
        I.append(['讲解', f'{t["zh"]} · {tt}', plain(body)[:900], u + '#' + sid])
for slug, n, zh, ja, lead, hero, secs, sub in PAGES[:3]:
    kind = {'formulas': '公式', 'pitfalls': '易错', 'tips': '技巧'}[slug]
    if slug == 'tips':
        for sid, tt, j, body in secs:
            for m in re.finditer(r'<article class="q tip" id="(tip\d+)"><div class="q-head"><b>(.*?)</b>(.*?)</article>', body, re.S):
                I.append([kind, detex(plain(m.group(2))), detex(plain(m.group(3)))[:700], f'topics/{slug}/#{m.group(1)}'])
        continue
    for sid, tt, j, body in secs:
        if slug == 'pitfalls':
            for m in re.finditer(r'<article class="q pit" id="(pit\d+)"><div class="q-head"><b>(.*?)</b>.*?</div>(.*?)</article>', body, re.S):
                I.append([kind, plain(m.group(2)), plain(m.group(3))[:600], f'topics/{slug}/#{m.group(1)}'])
        else: I.append([kind, f'公式 · {tt}', plain(j + ' ' + body)[:900], f'topics/{slug}/#{sid}'])
open('assets/search.json', 'w').write(json.dumps(I, ensure_ascii=False, separators=(',', ':')))
# —— nav.js ——
nav = open('assets/nav.js').read().split('\n')
T = json.loads(re.match(r'\(function\(\)\{var T=(.*);$', nav[0]).group(1))
T = [x for x in T if x['slug'] not in EX] + [dict(n=n, slug=slug, zh=zh, ja=ja, ready=True) for slug, n, zh, ja, *_ in PAGES]
nav[0] = '(function(){var T=' + json.dumps(T, ensure_ascii=False) + ';'
open('assets/nav.js', 'w').write('\n'.join(nav))
# —— 首页：整页由 tools/build_home.py 生成（目次、导图、附里的速查工具块、加权排行表、组合热力图），这里重跑一遍，易错点条数与技巧招数随之更新 ——
import build_home
build_home.main()
print(len(TOP), 'topics', len(I), 'index entries', sum(1 for x in I if x[0] == '术语'), 'terms', sum(1 for x in I if x[0] == '题'), 'questions')
# —— MWG：再跑一遍页面补丁（幂等），保证生成页带 SRI、meta color-scheme、头脚本与设计层 ——
assert MWG.main() == 0, 'apply_mwg_polish found problems'
