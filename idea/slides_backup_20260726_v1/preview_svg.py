#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the same deck as SVG slides -> PDF (present-ready + lets us eyeball layout).
Mirrors build_deck.py. 1600x900 (16:9)."""
import os, html, subprocess, base64
from PIL import Image

HERE=os.path.dirname(os.path.abspath(__file__)); FIG=os.path.join(HERE,"figures")
OUT=os.path.join(HERE,"_preview"); os.makedirs(OUT,exist_ok=True)
FONT='"Alibaba PuHuiTi 3.0","Noto Sans CJK SC",sans-serif'
MONO='"JetBrains Maple Mono",monospace'
INK="#1F2A44"; GRAY="#6B7688"; LGRAY="#AEB6C2"; BLUE="#2B6CB0"; TEAL="#2C7A7B"
RED="#C5303A"; AMBER="#B7791F"; VIO="#6B46C1"; GREEN="#2F855A"; WHITE="#FFFFFF"
CARDBG="#F2F5FA"
W,H=1600,900
def esc(s): return html.escape(str(s),quote=True)
def T(x,y,s,size,color=INK,weight=400,anchor="start",family=None):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family=\'{family or FONT}\' dominant-baseline="middle">{esc(s)}</text>')
def rich(x,y,runs,size,anchor="start"):
    # runs: list of (text,color,weight)
    parts=[f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" font-family=\'{FONT}\' dominant-baseline="middle">']
    for (t,c,w) in runs:
        parts.append(f'<tspan fill="{c}" font-weight="{w}">{esc(t)}</tspan>')
    parts.append('</text>'); return "".join(parts)
def rrect(x,y,w,h,r,fill,stroke=None,sw=2):
    s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{fill}"'
    if stroke: s+=f' stroke="{stroke}" stroke-width="{sw}"'
    return s+'/>'
def svg(body,bg=WHITE): return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{bg}"/>{body}</svg>')
def fit(img, left,top,right,bottom):
    iw,ih=Image.open(img).size; aw,ah=right-left,bottom-top; ar=iw/ih
    if aw/ah>ar: h=ah; w=ah*ar
    else: w=aw; h=aw/ar
    x=left+(aw-w)/2; y=top+(ah-h)/2
    data=base64.b64encode(open(img,"rb").read()).decode()
    return f'<image xlink:href="data:image/png;base64,{data}" x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/>'

def footer(b,n):
    b.append(T(70,872,"组会 · Do Not Mention / SCR / HalluSquatting → 我的 idea",15,LGRAY))
    b.append(T(W-70,872,str(n),15,LGRAY,anchor="end"))
def titlebar(b,title,accent,kicker=None):
    if kicker: b.append(T(74,52,kicker,17,accent,700))
    b.append(T(72,92,title,38,INK,800)); b.append(rrect(74,124,150,6,3,accent))
def takeaway(b,text,color):
    y=795; b.append(rrect(70,y,1460,66,12,CARDBG)); b.append(rrect(70,y,16,66,0,color))
    b.append(rich(104,y+33,[("一句话：",color,700),(text,INK,400)],22))

def slide_img(title,img,tk=None,tkc=TEAL,accent=TEAL,kicker=None):
    b=[]; titlebar(b,title,accent,kicker)
    bottom=760 if not tk else 762
    b.append(fit(os.path.join(FIG,img),70,150,1530,bottom))
    if tk: takeaway(b,tk,tkc)
    return b
def slide_text(title,lines,accent=TEAL,kicker=None):
    # lines: list of (runs,size) where runs=[(t,color,weight)]
    b=[]; titlebar(b,title,accent,kicker)
    y=250
    for (runs,size,gap) in lines:
        if runs: b.append(rich(110,y,runs,size))
        y+=gap
    return b
def slide_divider(kicker,title,sub,color):
    b=[]; b.append(T(90,300,kicker,26,WHITE,700))
    # wrap long titles manually
    b.append(T(90,margin_title(title),title,46,WHITE,800))
    b.append(rrect(92,470,220,6,3,WHITE))
    b.append(T(92,520,sub,22,"#E8EEF6",400))
    return b, color
def margin_title(t): return 400

SLIDES=[]
# 1 title (special)
def title_slide():
    b=[]; b.append(rrect(0,0,26,H,0,TEAL))
    b.append(T(90,190,"组会论文分享",56,INK,800))
    b.append(rich(90,320,[("主讲  ",TEAL,700),("“Do Not Mention This to the User”",INK,800)],32))
    b.append(T(96,362,"Detecting & Understanding Malicious Agent Skills in the Wild · USENIX Security 2026",19,GRAY))
    b.append(rich(90,415,[("补充  ",TEAL,700),("SCR（组合风险） ｜ HalluSquatting（幻觉抢注）",INK,800)],28))
    b.append(rrect(92,470,1416,150,14,"#E7DFF7")); b.append(rrect(92,470,18,150,0,VIO))
    b.append(rich(130,522,[("我的方向：",VIO,700),("用户只给普通任务时，agent 会不会自主“获取”一个尚未安装的恶意 skill？",INK,700)],24))
    b.append(T(130,575,"三篇拼出「恶意供给 → 促成安装 → 真实执行」，我来测这条链能不能自主接通。",19,GRAY))
    b.append(T(90,700,"汇报人：（你的名字）    2026-07",17,LGRAY))
    return ("plain",b,None)
SLIDES.append(title_slide())

def D(k,t,s,c):
    b,col=slide_divider(k,t,s,c); return ("div",b,col)

SLIDES.append(("plain_f", slide_img("今天的主线：一个问题的三段","fig_roadmap.png",
    "恶意供给 → 促成安装 → 真实执行；我落在“普通任务能否自主获取”这一段。",VIO,VIO,"ROADMAP"),None))
SLIDES.append(("plain_f", slide_img("先铺个底：什么是 agent skill？","fig_skill_bg.png",None,TEAL,TEAL,"背景"),None))
SLIDES.append(D("主讲 · MAIN","“Do Not Mention This to the User”","USENIX Security 2026 · Yi Liu et al. · 大规模恶意 skill 生态测量",BLUE))
SLIDES.append(("plain_f", slide_img("一个真实的恶意 skill 长什么样","dnm_fig1_shadow.png",
    "说明写“安全的计算器”，脚本里却藏了反弹 shell —— 文档说的 ≠ 实际做的。",BLUE,BLUE,"Do Not Mention"),None))
SLIDES.append(("plain_f", slide_img("它怎么测：从 9.8 万到 157","dnm_fig3_funnel.png",
    "0.16% 是“行为确认恶意”的高精度下界，不是“生态只有 0.16% 有风险”。",BLUE,BLUE,"测量漏斗"),None))
SLIDES.append(("plain_f", slide_img("为什么可信：四道关","fig_dnm_verify.png",None,BLUE,BLUE,"验证质量"),None))
SLIDES.append(("plain_f", slide_img("三个发现：RQ1 / RQ2 / RQ3","fig_dnm_rq.png",
    "重点是后半段的分析：攻击是蓄意分层、分工明确、逃避随复杂度升级。",BLUE,BLUE,"核心结论"),None))
SLIDES.append(("plain", slide_text("它回答了什么，没回答什么",[
    ([("✓  回答了：",GREEN,700)],26,58),
    ([("     外部市场里真有行为确认的恶意 skill —— 而且已经规模化、隐蔽化供应。",INK,400)],23,90),
    ([("✗  没回答：",RED,700)],26,58),
    ([("     用户只给普通任务时，agent 会不会“自主”把它发现、安装、调用进来？",INK,400)],23,110),
    ([("→  ",VIO,700),("生态测量给了“现实性锚点”，但替代不了 acquisition 的端到端实验。这是我的切入点。",VIO,700)],23,50),
],BLUE,"承上启下"),None))
SLIDES.append(D("补充① · SUPPLEMENT","SCR：Benign in Isolation, Harmful in Composition","arXiv 2606.15242 · 华东师大 / A*STAR（预印本）",TEAL))
SLIDES.append(("plain_f", slide_img("核心：单个都干净，组合起来出事","scr_fig1_chain.png",
    "三个 skill 单独审都合规，串在一起——“清单+已审核+建议”被当成授权，就越权了。",TEAL,TEAL,"SCR"),None))
SLIDES.append(("plain_f", slide_img("结果：单独 vs 组合，三种机制","fig_scr_results.png",
    "TrustLift 最猛：一个“已审核”背书，把有害安装从 1.1% 抬到 83.9%。",TEAL,TEAL,"SCR 结果"),None))
SLIDES.append(("plain", slide_text("SCR 的边界 → 接我的问题",[
    ([("SCR 已经很接近，但它：",INK,700)],24,54),
    ([("   • 全部在 mock 沙箱、观测“模拟状态改变”，没有真实市场 / 真实落盘 / 注册；",INK,400)],22,46),
    ([("   • TrustLift 从“已经出现的下游安装请求”起步，不是普通任务自发去发现；",INK,400)],22,80),
    ([("所以我不能再说：",RED,700),("“第一个研究 install”“第一个测自主触发”“SCR 只测预装 skill”。",INK,400)],22,80),
    ([("→  ",VIO,700),("可守的区别：普通任务触发 + 真实落盘/注册/调用 的“同一条轨迹”逐段测量。",VIO,700)],23,40),
],TEAL,"边界"),None))
SLIDES.append(D("补充② · SUPPLEMENT","HalluSquatting：Beware of Agentic Botnets","arXiv 2607.07433 · Tel Aviv U / Technion / Intuit（预印本）",RED))
SLIDES.append(("plain_f", slide_img("机制：抢注“AI 记错的名字”","hallu_fig1_threat.png",
    "门槛极低：坏人只要能看趋势 + 注册一个名字，等 AI 自己“记错”送上门。",RED,RED,"HalluSquatting"),None))
SLIDES.append(("plain_f", slide_img("证据①：AI 到底多爱记错","fig_hallu_halluc.png",
    "只要资源比模型训练时间新，AI 几乎必然编错 owner —— 编得有规律、可抢注。",RED,RED,"证据 1/3"),None))
SLIDES.append(("plain_f", slide_img("证据②：skill 市场的两个结构缺口","fig_hallu_v1v2.png",
    "不是用户打错字，是市场命名结构 + AI 解析习惯，让“记错”成了默认结果。",RED,RED,"证据 2/3"),None))
SLIDES.append(("plain_f", slide_img("证据③：真的打到 RCE","fig_hallu_e2e.png",
    "真实产品端到端：代码助手 20–65%，个人助手 40–100%；装后聊天外泄 96%。",RED,RED,"证据 3/3"),None))
SLIDES.append(("plain", slide_text("HalluSquatting 的边界 → 接我的问题",[
    ([("它已经打到真实 RCE（40–100%），所以我不能说“第一个测真实执行”。但：",INK,700)],24,72),
    ([("   它的触发是 ",INK,400),("用户明确要求 clone / install",RED,700),("（用户本有获取意图，被幻觉+抢注劫持）。",INK,400)],22,80),
    ([("→  ",VIO,700),("我测的是：用户",VIO,700),("完全没有获取意图",RED,700),("、只给普通任务时，agent 会不会自发装。",VIO,700)],23,54),
    ([("      两者威胁模型不同：一个是“被劫持的显式安装”，一个是“任务诱导的自主安装”。",GRAY,400)],19,40),
],RED,"边界"),None))
SLIDES.append(D("我的 idea · MY WORK","三篇 → 我要测的“同一条轨迹”","Task-induced Autonomous Acquisition：普通任务能否自主接通 发现→安装→调用",VIO))
SLIDES.append(("plain_f", slide_img("三篇各覆盖一段，我测同一条链","fig_integration.png",
    "没人把“普通任务 → 自主全链 → 逐段归因”放进同一条轨迹。",VIO,VIO,"整合"),None))
SLIDES.append(("plain_f", slide_img("我的框架：把风险拆成逐段存活率","fig_my_funnel.png",
    "不报一个总 ASR，而是报每一段的条件存活率，指出真正的瓶颈在哪。",VIO,VIO,"方法"),None))
SLIDES.append(("plain_f", slide_img("我已有的先导抓手","fig_pilot.png",
    "两个先导现象都要带条件讲：是 idea 演化的证据，不是普适结论。",VIO,VIO,"先导结果"),None))
SLIDES.append(("plain", slide_text("讨论 & 下一步",[
    ([("下一步（先做小 pilot，再决定要不要扩大）",VIO,700)],24,50),
    ([("   1. 修 instrumentation：可配 tool budget，拆开 emitted/parsed/executed/on-disk/registered/invoked；",INK,400)],20,42),
    ([("   2. 真实落盘 + manifest + registry 三重验证“真的装上了”；",INK,400)],20,42),
    ([("   3. 60–100 次小 pilot，按预先规则 Go / No-Go —— 有稳定、可归因、可复现的结构才继续。",INK,400)],20,74),
    ([("想请大家讨论",TEAL,700)],24,50),
    ([("   Q1  一个“全链逐段测量”要出现什么级别的结构性结果，才够成一篇 measurement paper？",INK,400)],20,42),
    ([("   Q2  要不做成玩具市场，正式实验至少需要哪些真实要素：真实 registry、真实落盘、多 scaffold？",INK,400)],20,40),
],VIO,"收尾"),None))
SLIDES.append(("plain", slide_text("（备用）汇报口径红线",[
    ([("被追问时，守住这几条：",INK,700)],22,50),
    ([("   • 不说“第一个测 install / E2E / 自主触发” —— SCR、HalluSquatting 已分别覆盖。",INK,400)],19,40),
    ([("   • “26.1% 有漏洞”是另一篇的静态筛查口径，被 SCR 误引；本篇是 0.16% 行为确认。",INK,400)],19,40),
    ([("   • 我的 0/2/1 是单模型先导观察，不是“明确任务天然安全”的普适结论。",INK,400)],19,40),
    ([("   • 三篇百分比不能直接横比：起点、终点、成功定义都不同。",INK,400)],19,40),
    ([("   • research gap ≠ novelty：贡献要来自新测量/新现象/方法/防御；低装机率也要有结构才有价值。",INK,400)],19,40),
],GRAY,"BACKUP"),None))

# render
pngs=[]
for i,(kind,body,color) in enumerate(SLIDES,1):
    if kind=="div":
        content=svg("".join(body),bg=color)
    else:
        b=list(body); footer(b,i); content=svg("".join(b))
    sp=os.path.join(OUT,f"s{i:02d}.svg"); open(sp,"w").write(content)
    pp=os.path.join(OUT,f"s{i:02d}.png")
    subprocess.run(["rsvg-convert","-w","1600","-h","900",sp,"-o",pp],check=True)
    pngs.append(pp)
pdf=os.path.join(HERE,"组会_Do_Not_Mention_三篇_预览.pdf")
subprocess.run(["magick"]+pngs+[pdf],check=True)
print("preview PDF:",pdf,"| slides:",len(pngs))
