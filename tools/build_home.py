# 数学站：生成首页 index.html（教材目次 + 知识导图 + 附 + 表）。可重复运行，输出只由下面的数据决定：
#   assets/topics.txt（出题项目 1–18 的中日文名）、assets/bank_analysis.json（过去问加权・出现题数）、tools/home_freq.html（加权排行表与组合热力图）、
#   tools/math_data.py / math_tips.py（易错点条数、技巧招数）、tools/homemap.py（导图生成器，与化学・生物站同一份）。
#   python3 tools/build_home.py
# build_extras.py 末尾会调用本脚本的 main()，所以重建速查页不会冲掉首页；apply_mwg_polish.py 认得本脚本的输出（HOME_MARK），只做幂等的头部补丁。
# 样式：assets/eju-ds.css（共用设计层）之后再链接 assets/home.css（数学站首页目次块，只作用于 body.contents / #map）；交互：assets/map.js。
import os, re, sys, json, html, math
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.dont_write_bytecode = True  # 不在 tools/ 留 __pycache__
sys.path.insert(0, 'tools')
import apply_mwg_polish as MWG
from homemap import ico, render
import mapkids
from math_data import PF
from math_tips import TIPS
E = html.escape
HOME_MARK = '<!--home: tools/build_home.py-->'

# —— 专题 ——
TOP = {}
for l in open('assets/topics.txt', encoding='utf-8').read().strip().splitlines():
    n, slug, zh, ja, _ = l.split('|', 4); TOP[slug] = dict(n=int(n), num=n, slug=slug, zh=zh, ja=ja, href=f'topics/{slug}/')
TOP['differentiation'] = dict(n=19, num='19', slug='differentiation', zh='微分（真题风格专题）', ja='微分法の応用', href='topics/differentiation/')
TOP['integration'] = dict(n=20, num='20', slug='integration', zh='积分（真题风格专题）', ja='積分法の応用', href='topics/integration/')
CLAUDE = dict(num='19–20', zh='微分法与积分法', ja='微分法・積分法', href='claude/', meta='讲义：从导数到定积分的应用')
_A = json.load(open('assets/bank_analysis.json')); NQ = len(_A['entries'])
W, APP = {}, {}
for e in _A['entries']:
    for k, v in e['topics'].items(): W[k] = W.get(k, 0) + v; APP[k] = APP.get(k, 0) + 1
def stars(w): return '★★★' if w >= 20 else '★★' if w >= 8 else '★' if w > 0 else '—'  # 与各专题页「出题频度」相同：加权 ≥20 / 8–20 / <8

CHAPTERS = [  # 章名、日文名、导图上的短名、提要、所含专题（按讲义顺序）
 ('数与式・集合', '数と式・集合', '数与式', '整式与实数的计算、集合与命题、整数的性质，以及多项式除法、二项式定理、等式与不等式的证明、高次方程式。',
  ['numbers-expressions', 'sets-logic', 'integers', 'expressions-equations']),
 ('函数', '関数', '函数', '二次函数的图像与最值，指数函数与对数函数，三角函数与加法定理，分式函数、无理函数与反函数・合成函数。',
  ['quadratic-functions', 'exp-log', 'trig-functions', 'functions']),
 ('图形', '図形', '图形', '三角比与正弦・余弦定理，平面与空间图形的性质，坐标平面上的直线、圆与区域，二次曲线、参数方程与极坐标。',
  ['trig-ratios', 'plane-solid-geometry', 'coordinate-geometry', 'curves']),
 ('计数与概率', '場合の数と確率', '概率', '排列与组合、独立试行与条件概率、期望值；随机变量的分布、期望・方差与二项分布。',
  ['counting-probability', 'probability-distributions']),
 ('数列・向量・复数', '数列・ベクトル・複素数平面', '数列向量', '等差・等比数列与 Σ、递推式与数学归纳法；平面与空间向量、内积与向量方程；复数平面、极形式与棣莫弗定理。',
  ['sequences', 'vectors', 'complex-plane']),
 ('极限与微积分', '極限・微分法・積分法', '微积分', '数列与函数的极限、连续性；导数与切线、增减与极值；不定积分与定积分、面积与体积。',
  ['limits', 'differentiation', 'integration']),
]
assert sorted(s for c in CHAPTERS for s in c[4]) == sorted(TOP), '目次分组要覆盖全部 20 个出题项目'

# —— 目次 ——
def _stars(s): return f'<span class="stars" aria-label="重要度 {len(s)}/3">{s}</span>' if s != '—' else '<span class="stars" aria-label="过去问未出">—</span>'
def _row(num, zh, ja, href, meta):
    return (f'<li><a href="{href}"><span class="ct-n">{num}</span><span class="ct-t"><span class="ct-zh">{zh}</span>'
            f'<span class="ct-ja" lang="ja">{ja}</span></span><span class="ct-dots" aria-hidden="true"></span><span class="ct-m">{meta}</span></a></li>')
def _entry(t):
    w = W.get(t['slug'], 0)
    return _row(t['num'], t['zh'], t['ja'], t['href'], f'<span class="ct-w">加权 {w:.1f}</span><span class="ct-sep"> · </span>出现 {APP.get(t["slug"], 0)} 题 {_stars(stars(w))}')
def chapters():
    out = []
    for k, (name, ja, _, intro, slugs) in enumerate(CHAPTERS, 1):
        rows = ''.join(_entry(TOP[s]) for s in slugs)
        if 'differentiation' in slugs:  # 19–20 的讲义版排在两个真题风格专题之前（与改版前的目录顺序相同）
            i = rows.index('<li><a href="topics/differentiation/">')
            rows = rows[:i] + _row(CLAUDE['num'], CLAUDE['zh'], CLAUDE['ja'], CLAUDE['href'], CLAUDE['meta']) + rows[i:]
        wsum = sum(W.get(s, 0) for s in slugs)
        out.append(f'<li class="ct-part"><p class="ct-no" aria-hidden="true">{k}</p><div class="ct-body">'
                   f'<h3 id="ch-{k}"><span class="ct-vh">第 {k} 章　</span>{name}<span class="ct-chja" lang="ja">{ja}</span></h3>'
                   f'<p class="ct-intro">{intro}<span class="ct-sum">{len(slugs)} 个专题 · 过去问加权 {wsum:.1f} 题</span></p>'
                   f'<ol class="ct-list">{rows}</ol></div></li>')
    return ''.join(out)

# —— 知识导图 ——
# 代表式取自 tools/math_data.py（公式速查）或各专题页抬头的式子；记法见 homemap.fml（` 直立、~ 粗体向量、函数名自动直立）
XLINKS = [  # (slug, slug, 弧上标签, 图注里的全称)
 ('quadratic-functions', 'differentiation', '切线与极值'), ('limits', 'differentiation', '导数定义', '导数的定义'),
 ('differentiation', 'integration', '基本定理', '微积分基本定理'), ('sequences', 'limits', '数列的极限'),
 ('vectors', 'coordinate-geometry', '向量方程', '向量方程与图形'), ('complex-plane', 'trig-functions', '极形式'),
 ('trig-ratios', 'trig-functions', '一般角', '三角比推广到一般角'), ('counting-probability', 'probability-distributions', '二项分布'),
]
MAPF = {
 'numbers-expressions': '√a^2 = |a|',                  # 专题页抬头 / math_data
 'sets-logic': '(p ⇒ q) ⇔ (q̄ ⇒ p̄)',                    # 专题页抬头：对偶
 'integers': 'ab = GL',                                # math_data：最大公约数・最小公倍数
 'expressions-equations': 'α + β = −b/a',              # 专题页抬头 / math_data：根与系数的关系
 'quadratic-functions': 'y = a(x − p)^2 + q',          # 专题页抬头 / math_data
 'exp-log': 'a^p = M ⇔ p = log_a M',                   # 专题页抬头
 'trig-functions': 'sin 2α = 2 sin α cos α',           # math_data：倍角公式
 'functions': 'y = k/(x − p) + q',                     # 专题页抬头：分式函数
 'trig-ratios': 'a^2 = b^2 + c^2 − 2bc cos A',         # 专题页抬头 / math_data：余弦定理
 'plane-solid-geometry': 'v − e + f = 2',              # 专题页抬头 / math_data：欧拉多面体定理
 'coordinate-geometry': '(x − a)^2 + (y − b)^2 = r^2', # 专题页抬头 / math_data
 'curves': 'x^2/a^2 + y^2/b^2 = 1',                    # 专题页抬头 / math_data：椭圆
 'counting-probability': '_n`C`_r = n!/(r!(n − r)!)',  # 专题页抬头 / math_data
 'probability-distributions': 'V(X) = E(X^2) − {E(X)}^2',  # 专题页抬头 / math_data
 'sequences': 'a_n = a + (n − 1)d',                    # math_data：等差数列
 'vectors': '~a·~b = |~a||~b| cos θ',                  # 专题页抬头 / math_data：内积
 'complex-plane': 'z = r(cos θ + i sin θ)',            # 专题页抬头 / math_data：极形式
 'limits': 'lim_{x→a} f(x) = f(a)',                    # 专题页抬头：连续
 'differentiation': 'y − f(t) = f′(t)(x − t)',         # 专题页抬头 / math_data：切线
 'integration': 'S = ∫_a^b {f(x) − g(x)} dx',          # 专题页抬头 / math_data：面积
}
MAPL = {'trig-ratios': '三角比', 'expressions-equations': '各种式', 'functions': '分式・反函数', 'exp-log': '指数与对数',
        'differentiation': '微分法', 'integration': '积分法', 'counting-probability': '排列组合与概率'}
def _icon_numline(x, y, s):  # 数轴：箭头、刻度，√2 与 −1 处的点，上方一段区间（不等式的解）
    return ico(x, y, s, lambda P, R: f'<path d="M{P(.04, .62)}H{x + .94 * s:.1f}M{P(.88, .58)}L{P(.95, .62)}L{P(.88, .66)}"/>'
               f'<path class="mp-thin" d="' + ''.join(f'M{P(u, .58)}V{y + .66 * s:.1f}' for u in (.14, .3, .46, .62, .78)) + f'M{P(.3, .4)}H{x + .68 * s:.1f}"/>'
               f'<circle class="mp-dot" cx="{x + .3 * s:.1f}" cy="{y + .4 * s:.1f}" r="{R(.03)}"/><circle class="mp-ion" cx="{x + .68 * s:.1f}" cy="{y + .4 * s:.1f}" r="{R(.03)}"/>'
               f'<text class="mp-sub" x="{x + .46 * s:.1f}" y="{y + .84 * s:.1f}" text-anchor="middle">0</text><text class="mp-sub" x="{x + .14 * s:.1f}" y="{y + .84 * s:.1f}" text-anchor="middle">−1</text>')
def _icon_parabola(x, y, s):  # y = x² 的抛物线 + 坐标轴 + 顶点
    return ico(x, y, s, lambda P, R: f'<path class="mp-thin" d="M{P(.04, .82)}H{x + .96 * s:.1f}M{P(.5, .96)}V{y + .04 * s:.1f}"/>'
               f'<path d="M{P(.16, .1)}' + ''.join(f'L{P(.16 + .68 * i / 32, .82 - .72 * ((i / 32 * 2 - 1) ** 2))}' for i in range(1, 33)) + '"/>'
               f'<circle class="mp-dot" cx="{x + .5 * s:.1f}" cy="{y + .82 * s:.1f}" r="{R(.03)}"/>')
def _icon_circle(x, y, s):  # 坐标轴上的圆与内接三角形
    c = (.5, .5); r = .32; pt = lambda a: (c[0] + r * math.cos(math.radians(a)), c[1] - r * math.sin(math.radians(a)))
    A, B, C_ = pt(110), pt(210), pt(-20)
    return ico(x, y, s, lambda P, R: f'<path class="mp-thin" d="M{P(.04, .5)}H{x + .96 * s:.1f}M{P(.5, .96)}V{y + .04 * s:.1f}"/>'
               f'<circle cx="{x + c[0] * s:.1f}" cy="{y + c[1] * s:.1f}" r="{R(r)}"/><path d="M{P(*A)}L{P(*B)}L{P(*C_)}Z"/>')
def _icon_dice(x, y, s):  # 树形图：一次试行分两支、再各分两支（排列组合与概率的数法）
    pts = {'o': (.1, .5), 'a': (.45, .26), 'b': (.45, .74), 'aa': (.85, .14), 'ab': (.85, .38), 'ba': (.85, .62), 'bb': (.85, .86)}
    ed = [('o', 'a'), ('o', 'b'), ('a', 'aa'), ('a', 'ab'), ('b', 'ba'), ('b', 'bb')]
    return ico(x, y, s, lambda P, R: '<path class="mp-thin" d="' + ''.join(f'M{P(*pts[u])}L{P(*pts[v])}' for u, v in ed) + '"/>'
               + ''.join(f'<circle class="{"mp-dot" if len(k) < 2 else "mp-ion"}" cx="{x + u * s:.1f}" cy="{y + v * s:.1f}" r="{R(.035 if len(k) < 2 else .045)}"/>' for k, (u, v) in pts.items()))
def _icon_vector(x, y, s):  # 复数平面上的向量：实轴、虚轴、从原点出发的箭头与辐角弧
    tip = (.82, .24); o = (.18, .8); ang = math.atan2(o[1] - tip[1], tip[0] - o[0])
    hd = [(tip[0] - .09 * math.cos(ang + d), tip[1] + .09 * math.sin(ang + d)) for d in (.4, -.4)]
    return ico(x, y, s, lambda P, R: f'<path class="mp-thin" d="M{P(.06, .8)}H{x + .96 * s:.1f}M{P(.18, .96)}V{y + .04 * s:.1f}"/>'
               f'<path d="M{P(*o)}L{P(*tip)}M{P(*hd[0])}L{P(*tip)}L{P(*hd[1])}"/>'
               f'<path class="mp-thin" d="M{P(.38, .8)}A{R(.2)} {R(.2)} 0 0 0 {P(o[0] + .2 * math.cos(ang), o[1] - .2 * math.sin(ang))}"/>'
               f'<text class="mp-it" x="{x + .5 * s:.1f}" y="{y + .74 * s:.1f}">θ</text>')
def _icon_tangent(x, y, s):  # 曲线 + 切线 + 曲线下的面积（竖线排成的阴影）
    f = lambda u: .78 - .55 * math.sin(math.pi * (u - .08) / 1.0) ** 2 * (u < 1.08)
    t0 = .38; d = (f(t0 + .001) - f(t0 - .001)) / .002
    return ico(x, y, s, lambda P, R: f'<path class="mp-thin" d="M{P(.04, .88)}H{x + .96 * s:.1f}M{P(.08, .96)}V{y + .04 * s:.1f}'
               + ''.join(f'M{P(u, .88)}V{y + f(u) * s:.1f}' for u in (.58, .64, .7, .76, .82)) + '"/>'
               f'<path d="M{P(.08, f(.08))}' + ''.join(f'L{P(.08 + .86 * i / 32, f(.08 + .86 * i / 32))}' for i in range(1, 33)) + '"/>'
               f'<path class="mp-thin" d="M{P(t0 - .2, f(t0) - .2 * d)}L{P(t0 + .2, f(t0) + .2 * d)}"/><circle class="mp-dot" cx="{x + t0 * s:.1f}" cy="{y + f(t0) * s:.1f}" r="{R(.03)}"/>')
ICONS = [_icon_numline, _icon_parabola, _icon_circle, _icon_dice, _icon_vector, _icon_tangent]
MAPCFG = dict(subject='数学', subject_ja='数学', cap_ja='図　数学の体系', start=160, MINSEC=1.5,
              W=1300, H=1380, CX=650, CY=666, R0=60, R1=220, R2=400, NR=46, IS=60, FN=16, FF=14.5, FSUB=10.5, FL=14.5, BH=52, GAP=11, FCH=21)
def _topic_lead(slug):
    p = os.path.join('topics', slug, 'index.html')
    if not os.path.exists(p):
        return ''
    m = re.search(r'<p class="lead">(.*?)</p>', open(p, encoding='utf-8').read(), re.S)
    if not m:
        return ''
    text = html.unescape(re.sub(r'<[^>]+>', '', m.group(1)))
    text = ' '.join(text.split())
    # 去掉各讲义页共用的收尾套话，保留前面的内容本身
    text = re.split(r'[：。，]每个知识点', text)[0]
    text = re.sub(r'[：，。](?:再|最后)?用原创的 EJU.*$', '', text)
    text = re.sub(r'[：，。]日语术语随文标注.*$', '', text)
    text = text.strip('：:，,、 ')
    if text and not text.endswith(('。', '！', '？')):
        text += '。'
    def _plain(m):
        x = m.group(1)
        x = x.replace(r'^\circ', '°').replace(r'\circ', '°').replace(r'\sim', '～').replace(r'\Sigma', 'Σ').replace(r'\cdot', '·')
        return x
    return re.sub(r'\$([^$]+)\$', _plain, text)
def _mapdata():
    chs, tps = {}, {}
    for k, (name, ja, _sh, intro, slugs) in enumerate(CHAPTERS, 1):
        chs[str(k)] = {'zh': name, 'ja': ja, 'intro': intro, 'href': f'#ch-{k}'}
        for s in slugs:
            top = TOP[s]
            tps[s] = {'zh': top['zh'], 'ja': top.get('ja') or '', 'intro': _topic_lead(s), 'href': f'topics/{s}/', 'ch': str(k), 'children': mapkids.kids_from_html(open(os.path.join('topics', s, 'index.html'), encoding='utf-8').read() if os.path.exists(os.path.join('topics', s, 'index.html')) else '', s)}
    s = json.dumps({'subject': '数学', 'chapters': chs, 'topics': tps}, ensure_ascii=False, separators=(',', ':'))
    out = s.replace('<', '\\u003c')
    _nk = sum(len(v.get('children') or []) for v in tps.values())
    print('map kids:', _nk)
    return out

def knowledge_map():
    chs = [dict(name=name, ja=ja, short=sh, icon=ICONS[k],
                topics=[dict(TOP[s], label=MAPL.get(s, TOP[s]['zh']), f=MAPF[s]) for s in slugs])
           for k, (name, ja, sh, _, slugs) in enumerate(CHAPTERS)]
    return render(dict(MAPCFG, chapters=chs, xlinks=XLINKS))

# —— 附・表 ——
def appendix():
    rows = [('21', '公式速查', '公式集', 'topics/formulas/', '按专题的核心公式与成立条件'),
            ('22', '易错点・陷阱', '間違えやすいポイント', 'topics/pitfalls/', f'{len(PF)} 条常见错误与例子'),
            ('24', '快速解题技巧', '速解テクニック', 'topics/tips/', f'{len(TIPS)} 招 · 按出题频度排序'),
            ('23', '站内搜索', 'サイト内検索', 'topics/search/', '讲解・练习・公式・易错点・术语'),
            ('—', '过去问知识点浏览', '過去問エクスプローラー', 'explorer/', f'{NQ} 题逐题的知识点构成'),
            ('—', '微积分 Codex 版（另一种设计）', '別バージョン', 'codex/', '其他版本')]
    return '<!--X-ANCHOR--><!--X-BEGIN-->' + ''.join(_row(*r) for r in rows) + '<!--X-END-->'
def tables():
    src = open('tools/home_freq.html', encoding='utf-8').read()
    style = re.search(r'<style id="mathfreq">.*?</style>', src, re.S).group(0)
    out = []
    for sid, no, ja, hid in (('freq-rank', '表', '出題分析', 'h-rank'), ('cooc', '表', '組み合わせ', 'h-cooc')):
        m = re.search(rf'<section id="{sid}"><h2>(.*?)</h2><p>(.*?)</p>(<div class="tw[^"]*">.*?</table></div>)</section>', src, re.S)
        if not m: raise SystemExit(f'tools/home_freq.html 里找不到 #{sid}')
        out.append(f'<section id="{sid}" aria-labelledby="{hid}"><div class="ct-part"><p class="ct-no ct-no-a" aria-hidden="true">{no}</p><div class="ct-body">'
                   f'<h2 id="{hid}">{m.group(1)}<span class="ct-chja" lang="ja">{ja}</span></h2><p class="ct-intro">{m.group(2)}</p>{m.group(3)}</div></div></section>')
    return style, ''.join(out)

SITES = [('https://feather0000.github.io/eju-physics/', 'EJU 理科 物理'), ('https://feather0000.github.io/eju-chemistry/', 'EJU 理科 化学'), ('https://feather0000.github.io/eju-biology/', 'EJU 理科 生物')]
PREFACE = ('这是按 JASSO《日本留学試験 数学シラバス》（2026 年度第 1 回起适用）出题项目 1–20 整理的中文讲义，按教材的顺序合为六章。'
           '建议先读各专题的讲解和例题，再做练习；公式速查、易错点和解题技巧可以随时翻。'
           '右侧的「出现 N 题」是 2005–2025 年过去问中涉及该专题的题数，「加权」按每题各小问的填空数折算（每题合计 1）；拿不准先看哪一章时可以参考它们，详细排行见本页最后的表。')

def page():
    svg, legend, stat = knowledge_map()
    mapdata = _mapdata()
    style, tbl = tables()
    head = (f'<!doctype html>\n<html lang="zh-Hans" data-site="{MWG.SITE}">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<meta name="color-scheme" content="light dark">\n{MWG.HEADJS}\n<title>EJU 数学コース2 全专题讲解</title>\n'
            f'<meta name="description" content="{E(MWG.SITE_DESC)}">\n{style}\n<link rel="stylesheet" href="assets/eju-ds.css">\n<link rel="stylesheet" href="assets/home.css">\n</head>\n')
    body = f'''<body class="home contents">{HOME_MARK}
<a class="skip" href="#chapters">跳到目次</a>
<div class="ct-wrap">
<header class="ct-head">
<div class="ct-top"><p class="ct-kicker">EJU 数学 · コース2</p>{MWG.BTN}</div>
<h1>数学コース2<br>全专题讲解</h1>
<div class="ct-preface"><p>{PREFACE}</p>
<p class="ct-facts">共 20 个出题项目专题，另有 19–20 的微积分讲义；过去问 {NQ} 题已逐题拆分到知识点。</p></div>
</header>
<main id="main">
<section id="chapters" aria-labelledby="h-chapters"><h2 id="h-chapters" class="ct-label">目次<span lang="ja">もくじ</span></h2>
<ol class="ct-parts">{chapters()}</ol></section>
<section id="map" aria-labelledby="h-map"><div class="ct-part"><p class="ct-no ct-no-a" aria-hidden="true">图</p><div class="ct-body">
<h2 id="h-map">知识导图<span class="ct-chja" lang="ja">知識マップ</span></h2>
<p class="ct-intro">中心「数学」分出六章，每章一色，外圈是 20 个出题项目和一条代表式；虚线弧标出专题之间的重要联系。点章节或专题可放大查看简介，再从说明卡进入对应页。</p></div>
<figure class="mp"><p class="mp-hint" id="mp-hint">点节点可放大查看简介。电脑上按住 Ctrl 或 ⌘ 滚动缩放；点进图中后可拖动。触屏用双指缩放。Esc 或「返回」还原。</p>
<div class="mp-scroll" role="region" aria-label="知识导图" aria-describedby="mp-hint">{svg}</div>
<figcaption id="mp-cap">数学知识导图：中心「数学」分出六章，各章外圈列出题项目与代表式。虚线弧所示的联系：<ul class="mp-legend">{legend}</ul></figcaption></figure><script type="application/json" id="mp-data">{mapdata}</script></div></section>
<section id="appendix" aria-labelledby="h-appendix"><div class="ct-part"><p class="ct-no ct-no-a" aria-hidden="true">附</p><div class="ct-body">
<h2 id="h-appendix">速查与工具<span class="ct-chja" lang="ja">資料・ツール</span></h2>
<p class="ct-intro">考前查公式、找易错点、练速解技巧；站内搜索覆盖讲解、练习、公式与术语。过去问浏览器可以按专题筛选每道题的知识点构成。</p>
<ol class="ct-list">{appendix()}</ol></div></div></section>
{tbl}
</main>
<footer class="ct-foot"><p class="ct-sites">EJU 理科：{"".join(f'<a href="{u}">{a}</a>' for u, a in SITES)}</p><p>原创讲义与题目，非 JASSO 官方内容。按《日本留学試験 数学シラバス（コース2）》编排。</p></footer>
</div>
<script src="assets/vendor/d3-eju.min.js"></script><script src="assets/map.js"></script>{MWG.TOGGLEJS}<script src="assets/nav.js"></script></body></html>
'''
    s = MWG.headmeta(head + body, '', '', ux=False)  # favicon、OG / Twitter 卡片（与 apply_mwg_polish 的 brand() 同一函数）
    return s, stat

def main():
    s, stat = page()
    if MWG.home(s) != s: raise SystemExit('build_home：输出与 apply_mwg_polish.home() 不一致（补丁会改动首页）')
    p = MWG.problems('index.html', s)
    if p: raise SystemExit(f'build_home：{p}')
    open('index.html', 'w').write(s)
    print('home ok:', stat)

if __name__ == '__main__':
    main()
