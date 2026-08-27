#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate custom slide figures as SVG (rendered to PNG by rsvg-convert).
Design system: clean, few words, big numbers — matches an image-first talk.
All numbers are source-verified (see idea/27 & idea/28 原文核对 blocks)."""
import math, os, html, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)

FONT = '"Alibaba PuHuiTi 3.0","Noto Sans CJK SC","Noto Sans CJK HK",sans-serif'
MONO = '"JetBrains Maple Mono","Noto Sans Mono",monospace'

# palette
INK   = "#1F2A44"   # near-black navy (titles)
GRAY  = "#6B7688"   # secondary text
LGRAY = "#AEB6C2"
CARD  = "#EEF2F7"   # light card fill
LINE  = "#CBD5E0"
BLUE  = "#2B6CB0"   # Do Not Mention / supply
BLUEL = "#DCE8F6"
TEAL  = "#2C7A7B"   # SCR / method
TEALL = "#D6EAEA"
RED   = "#C5303A"   # HalluSquatting / attack
REDL  = "#F7DDDF"
AMBER = "#B7791F"   # promotion / caution
AMBERL= "#FCEBCD"
GREEN = "#2F855A"   # benign / safe
GREENL= "#D7EBDF"
VIO   = "#6B46C1"   # MY work
VIOL  = "#E7DFF7"

def esc(s): return html.escape(str(s), quote=True)

def _svg(w, h, body, bg="#FFFFFF"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family=\'{FONT}\'>'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')

def rrect(x, y, w, h, r=14, fill=CARD, stroke=None, sw=2, dash=None, opacity=1):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{fill}" opacity="{opacity}"'
    if stroke: s += f' stroke="{stroke}" stroke-width="{sw}"'
    if dash: s += f' stroke-dasharray="{dash}"'
    return s + '/>'

def T(x, y, s, size=26, color=INK, weight=400, anchor="middle", family=None, spacing=None):
    f = family or FONT
    extra = f' letter-spacing="{spacing}"' if spacing else ''
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}" font-family=\'{f}\'{extra} '
            f'dominant-baseline="middle">{esc(s)}</text>')

def lines(x, y, arr, size=22, color=INK, weight=400, anchor="middle", lh=None, family=None):
    lh = lh or size + 8
    out = []
    for i, s in enumerate(arr):
        out.append(T(x, y + i * lh, s, size, color, weight, anchor, family))
    return "".join(out)

def arrow(x1, y1, x2, y2, color=INK, w=4, head=13):
    ang = math.atan2(y2 - y1, x2 - x1)
    # shorten line so it ends at base of head
    bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
    p1 = (x2, y2)
    p2 = (x2 - head * math.cos(ang - 0.42), y2 - head * math.sin(ang - 0.42))
    p3 = (x2 - head * math.cos(ang + 0.42), y2 - head * math.sin(ang + 0.42))
    return (f'<line x1="{x1}" y1="{y1}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round"/>'
            f'<polygon points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" fill="{color}"/>')

def chip(cx, cy, r, fill, num, tcolor="#FFFFFF"):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"/>' + T(cx, cy+1, num, r*1.05, tcolor, 700)

def write(name, w, h, body, bg="#FFFFFF"):
    p = os.path.join(ASSETS, name + ".svg")
    open(p, "w").write(_svg(w, h, body, bg))
    png = os.path.join(FIGDIR, name + ".png")
    subprocess.run(["rsvg-convert", "-z", "2", p, "-o", png], check=True)
    return p

# ----------------------------------------------------------------------------
# 1. ROADMAP — three-stage supply chain + my landing point
# ----------------------------------------------------------------------------
def fig_roadmap():
    W, H = 1680, 640
    b = []
    cards = [
        (BLUE, BLUEL, "①", "恶意供给 · 真实存在", "Do Not Mention", "真实市场里已有\n行为确认的恶意 skill"),
        (TEAL, TEALL, "②", "促成安装 · 组合放大", "SCR", "单独干净的 skill，\n组合/背书 → 有害安装"),
        (RED,  REDL,  "③", "真实执行 · 打到 RCE", "HalluSquatting", "幻觉+抢注 → 安装\n→ 远程代码执行"),
    ]
    cw, gap = 470, 90
    x0 = (W - (cw*3 + gap*2))//2
    top = 70
    ch = 300
    for i,(c,cl,n,title,paper,desc) in enumerate(cards):
        x = x0 + i*(cw+gap)
        b.append(rrect(x, top, cw, ch, 22, "#FFFFFF", c, 3))
        b.append(rrect(x, top, cw, 66, 22, c))
        b.append(rrect(x, top+44, cw, 22, 0, c))
        b.append(chip(x+46, top+33, 24, "#FFFFFF", n, c))
        b.append(T(x+cw/2+24, top+33, title.split(" · ")[0]+" · "+title.split(" · ")[1], 27, "#FFFFFF", 700))
        b.append(rrect(x+30, top+92, cw-60, 46, 12, cl))
        b.append(T(x+cw/2, top+115, paper, 27, c, 700, family=MONO))
        dl = desc.split("\n")
        b.append(lines(x+cw/2, top+185, dl, 25, INK, 500, lh=38))
        if i < 2:
            ax = x+cw+18
            b.append(arrow(ax, top+ch/2, ax+gap-36, top+ch/2, GRAY, 6, 18))
    # my landing band
    by = top+ch+52
    b.append(rrect(x0, by, cw*3+gap*2, 118, 20, VIOL, VIO, 3))
    b.append(rrect(x0, by, 150, 118, 20, VIO))
    b.append(rrect(x0+130, by, 20, 118, 0, VIO))
    b.append(lines(x0+75, by+44, ["我的","问题"], 30, "#FFFFFF", 800, lh=36))
    b.append(T(x0+185, by+42, "普通能力任务触发（用户零获取意图）、目标 skill 尚未安装时——", 27, INK, 600, anchor="start"))
    b.append(T(x0+185, by+82, "agent 会不会自主走完「发现 → 安装 → 调用」这条链？断在哪一段？", 27, VIO, 700, anchor="start"))
    write("fig_roadmap", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 2. WHAT IS AN AGENT SKILL (background)
# ----------------------------------------------------------------------------
def fig_skill_bg():
    W, H = 1560, 560
    b = []
    y = 150; bh = 150
    # user
    b.append(rrect(60, y, 200, bh, 18, CARD, LINE, 2))
    b.append(lines(160, y+58, ["用户"], 30, INK, 700))
    b.append(lines(160, y+100, ['“帮我装个','天气 skill”'], 21, GRAY, 400, lh=27))
    b.append(arrow(268, y+bh/2, 352, y+bh/2, GRAY, 5, 16))
    # agent
    b.append(rrect(360, y, 230, bh, 18, BLUEL, BLUE, 2.5))
    b.append(lines(475, y+55, ["Agent"], 30, BLUE, 800))
    b.append(lines(475, y+98, ["会规划、会调用工具", "开终端 / 读写文件 / 联网"], 19, INK, 400, lh=26))
    b.append(arrow(598, y+bh/2, 682, y+bh/2, GRAY, 5, 16))
    # marketplace
    b.append(rrect(690, y, 250, bh, 18, CARD, LINE, 2))
    b.append(lines(815, y+52, ["Skill 市场"], 29, INK, 700))
    b.append(lines(815, y+95, ["ClawHub / skills.rest", "公开 · 海量 · 少审核"], 19, GRAY, 400, lh=26))
    b.append(arrow(948, y+bh/2, 1032, y+bh/2, GRAY, 5, 16))
    # skill package
    b.append(rrect(1040, y-6, 300, bh+12, 18, "#FFFFFF", RED, 2.5))
    b.append(T(1190, y+22, "一个 skill 包", 25, RED, 800))
    b.append(rrect(1062, y+44, 256, 42, 9, GREENL))
    b.append(T(1190, y+65, "SKILL.md（给人看的说明）", 19, GREEN, 700))
    b.append(rrect(1062, y+94, 256, 42, 9, REDL))
    b.append(T(1190, y+115, "helper 脚本（真正执行）", 19, RED, 700))
    # bottom caption band
    b.append(rrect(60, 360, W-120, 150, 16, AMBERL))
    b.append(T(W/2, 398, "为什么危险 —— 三点", 26, AMBER, 800))
    pts = ["① 默认信任：装上几乎不问", "② 本地权限：等于你本人的权限", "③ 自然语言即攻击面：坏话写在 SKILL.md 里"]
    for i,p in enumerate(pts):
        b.append(T(120+i*470, 452, p, 22, INK, 600, anchor="start"))
    write("fig_skill_bg", W, H, "".join(b), bg="#FFFFFF")

# ----------------------------------------------------------------------------
# 3. SCR RESULTS — isolated vs composed, three mechanisms
# ----------------------------------------------------------------------------
def _barpair(x, gw, base, top_y, v_iso, v_comp, label, sub, note=None):
    out = []
    maxv = 100.0
    ch = base - top_y
    bw = 120
    def bar(bx, val, color, cap):
        num = 0.6 if isinstance(val, str) else val
        bh = max(6, ch * (num/maxv))
        out.append(rrect(bx, base-bh, bw, bh, 8, color))
        out.append(T(bx+bw/2, base-bh-26, cap, 30, color, 800))
    gx = x + (gw - (bw*2+50))/2
    bar(gx, v_iso, LGRAY, v_iso if isinstance(v_iso,str) else f"{v_iso}%")
    bar(gx+bw+50, v_comp, RED, v_comp if isinstance(v_comp,str) else f"{v_comp}%")
    out.append(arrow(gx+bw+6, base-16, gx+bw+44, base-16, GRAY, 4, 12))
    out.append(T(x+gw/2, base+34, label, 26, INK, 800))
    out.append(T(x+gw/2, base+66, sub, 19, GRAY, 500))
    if note: out.append(T(x+gw/2, base+92, note, 17, AMBER, 600))
    return "".join(out)

def fig_scr_results():
    W, H = 1560, 730
    b = []
    base, top_y = 470, 120
    # y-axis hint
    b.append(T(70, top_y, "100%", 18, LGRAY, 600, anchor="end"))
    b.append(T(70, base, "0", 18, LGRAY, 600, anchor="end"))
    b.append(f'<line x1="90" y1="{top_y}" x2="90" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    b.append(f'<line x1="90" y1="{base}" x2="{W-60}" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    gw = (W-160)//3
    b.append(_barpair(120,      gw, base, top_y, "≈0%", 33.6, "能力流 CapFlow", "隔离  →  组合", "DeepSeek-V4 >90%"))
    b.append(_barpair(120+gw,   gw, base, top_y, 1.1,   83.9, "信任转移 TrustLift", "无背书  →  有背书", "4/5 后端 ≥96.5%"))
    b.append(_barpair(120+2*gw, gw, base, top_y, 15.7,  27.0, "授权混淆 AuthBlur", "无关  →  授权语境", "相对 +71.8%"))
    # legend
    b.append(rrect(W/2-250, 600, 24, 24, 5, LGRAY)); b.append(T(W/2-212, 612, "单独/隔离", 21, INK, 600, anchor="start"))
    b.append(rrect(W/2-40, 600, 24, 24, 5, RED));    b.append(T(W/2-2, 612, "组合/背书后", 21, INK, 600, anchor="start"))
    b.append(T(W/2, 678, "单独看几乎无害；一旦组合或被“已审核”背书，风险跃升", 25, INK, 700))
    write("fig_scr_results", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 4. HALLU — hallucination rate new vs old
# ----------------------------------------------------------------------------
def fig_hallu_halluc():
    W, H = 1460, 620
    b = []
    base, top_y = 430, 110
    ch = base - top_y
    b.append(f'<line x1="120" y1="{base}" x2="{W-120}" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    def bar(cx, val, color, cap, sub):
        bw = 250
        bh = ch*(val/100)
        b.append(rrect(cx-bw/2, base-bh, bw, bh, 10, color))
        b.append(T(cx, base-bh-34, f"{val}%", 52, color, 800))
        b.append(T(cx, base+40, cap, 27, INK, 700))
        b.append(T(cx, base+74, sub, 20, GRAY, 500))
    bar(W*0.34, 92.4, RED,  "2025 新出的热门仓库", "AI 几乎必然编错 owner")
    bar(W*0.66, 0.9,  GREEN,"2013–18 老仓库（对照）", "训练数据里见过，记得住")
    b.append(rrect(W-560, 150, 470, 96, 14, AMBERL))
    b.append(lines(W-325, 182, ["规律：只要资源比模型训练时间新，", "幻觉就近乎必然、且可预测"], 21, AMBER, 700, lh=30))
    b.append(T(W/2, 560, "skill 安装场景同理，可高达 100% —— 坏人只要统计分布、抢先占坑", 24, INK, 700))
    write("fig_hallu_halluc", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 5. HALLU — two skill-install failure modes (V1 / V2)
# ----------------------------------------------------------------------------
def fig_hallu_v1v2():
    W, H = 1580, 600
    b = []
    def lane(y, tag, tagc, tagcl, user, mid, midnote, slug, reg):
        b.append(rrect(50, y, 120, 96, 14, tagc))
        b.append(lines(110, y+38, tag.split(" "), 30, "#FFFFFF", 800, lh=34))
        b.append(rrect(200, y+16, 360, 64, 12, CARD, LINE, 2))
        b.append(T(380, y+38, user, 22, INK, 600))
        b.append(T(380, y+64, "（用户说的）", 17, GRAY, 400))
        b.append(arrow(566, y+48, 640, y+48, tagc, 5, 15))
        b.append(rrect(648, y+16, 300, 64, 12, tagcl, tagc, 2))
        b.append(T(798, y+40, mid, 22, tagc, 800))
        b.append(T(798, y+66, midnote, 16, GRAY, 500))
        b.append(arrow(954, y+48, 1028, y+48, tagc, 5, 15))
        b.append(rrect(1036, y+16, 300, 64, 12, "#FFFFFF", RED, 2.5))
        b.append(T(1186, y+40, slug, 23, RED, 800, family=MONO))
        b.append(T(1186, y+66, reg, 16, RED, 600))
        b.append(arrow(1342, y+48, 1416, y+48, RED, 5, 15))
        b.append(rrect(1424, y+16, 108, 64, 12, REDL))
        b.append(lines(1478, y+38, ["坏人","占坑"], 20, RED, 800, lh=24))
    b.append(T(W/2, 60, "为什么 skill 安装“必然”被劫持：市场结构的两个缺口", 28, INK, 800))
    lane(150, "V1 掉词", TEAL, TEALL, 'install “skill-vetter”', "掉掉“skill”", "引导文里 skill 泛滥", "vetter", "80–100% 命中")
    lane(340, "V2 名不符实", BLUE, BLUEL, 'install “Baidu Wenku AIPPT”', "编一个名", "显示名≠真实 slug", "aippt-…（可占坑）", "复制标题即中招 100%")
    b.append(T(W/2, 500, "非英文文档的 skill 最惨：英文搜索把正牌挤出前 10，纠错路径也断了（100% 可占坑）", 22, AMBER, 700))
    write("fig_hallu_v1v2", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 6. HALLU — end-to-end RCE
# ----------------------------------------------------------------------------
def fig_hallu_e2e():
    W, H = 1480, 600
    b = []
    base, top_y = 430, 165
    ch = base-top_y
    b.append(f'<line x1="110" y1="{base}" x2="{W-560}" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    def rangebar(cx, lo, hi, cap, sub):
        bw=210
        y_hi = base-ch*(hi/100); y_lo = base-ch*(lo/100)
        b.append(rrect(cx-bw/2, y_hi, bw, base-y_hi, 10, REDL))
        b.append(rrect(cx-bw/2, y_hi, bw, y_lo-y_hi, 10, RED))
        b.append(T(cx, y_hi-30, f"{lo}–{hi}%", 40, RED, 800))
        b.append(T(cx, base+40, cap, 25, INK, 700))
        b.append(T(cx, base+72, sub, 19, GRAY, 500))
    rangebar(W*0.20, 20, 65, "代码助手（clone 仓库）", "Cursor/Windsurf/Cline… 6 个")
    rangebar(W*0.44, 40, 100, "个人助手（install skill）", "OpenClaw/ZeroClaw/NanoClaw")
    b.append(T((W*0.20+W*0.44)/2, 62, "真实产品上的端到端 RCE / 工具滥用成功率", 24, INK, 800))
    # right: post-install aggregate
    rx = W-500
    b.append(rrect(rx, 130, 440, 300, 18, INK))
    b.append(T(rx+220, 176, "装进去之后", 24, "#FFFFFF", 700))
    b.append(T(rx+120, 268, "96%", 76, "#FF8A8A", 800)); b.append(lines(rx+300, 250, ["聊天记录","外泄"], 24, "#FFFFFF", 600, lh=30))
    b.append(T(rx+120, 366, "84%", 76, "#FFC48A", 800)); b.append(lines(rx+300, 348, ["终端","反弹 shell"], 24, "#FFFFFF", 600, lh=30))
    b.append(T(W/2, 540, "受控分阶段验证：公开平台只注册良性替身，RCE 载荷在研究者本地机器上测", 21, AMBER, 700))
    write("fig_hallu_e2e", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 7. INTEGRATION — the centerpiece: lifecycle + 3 papers + my gap
# ----------------------------------------------------------------------------
def fig_integration():
    W, H = 1720, 920
    b = []
    stages = ["能力\n缺口","外部\n发现","发出\n安装","解析\n执行","落盘","注册","调用","载荷\n&任务"]
    n=len(stages); sw=176; sh=104; gap=14
    x0=(W-(sw*n+gap*(n-1)))//2
    py=470
    # pipeline chevrons
    xs=[]
    for i,s in enumerate(stages):
        x=x0+i*(sw+gap); xs.append(x)
        tip=22
        pts=f"{x},{py} {x+sw-tip},{py} {x+sw},{py+sh/2} {x+sw-tip},{py+sh} {x},{py+sh} {x+tip if i>0 else x},{py+sh/2}"
        b.append(f'<polygon points="{pts}" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>')
        b.append(lines(x+sw/2+ (tip/2 if i>0 else 0), py+sh/2 - (12 if "\n" in s else 0), s.split("\n"), 26, INK, 700, lh=30))
    def cx(i): return xs[i]+sw/2
    def bracket(i1, i2, yb, color, fill, paper, note, side="top"):
        x1=xs[i1]-4; x2=xs[i2]+sw+4
        h=58
        b.append(rrect(x1, yb, x2-x1, h, 12, fill, color, 2.5))
        b.append(T((x1+x2)/2, yb+22, paper, 24, color, 800, family=MONO))
        b.append(T((x1+x2)/2, yb+44, note, 18, INK, 500))
        # connector to pipeline
        midx=(x1+x2)/2
        if side=="top":
            b.append(f'<line x1="{midx}" y1="{yb+h}" x2="{midx}" y2="{py}" stroke="{color}" stroke-width="2" stroke-dasharray="4 4"/>')
        else:
            b.append(f'<line x1="{midx}" y1="{yb}" x2="{midx}" y2="{py+sh}" stroke="{color}" stroke-width="2" stroke-dasharray="4 4"/>')
    b.append(T(W/2, 56, "一条 Agent Skill 获取生命周期：三篇各覆盖一段，我测“同一条轨迹”", 30, INK, 800))
    # Do Not Mention — supply exists (left, before pipeline)
    b.append(rrect(x0-6, 150, 300, 92, 14, BLUEL, BLUE, 2.5))
    b.append(T(x0+144, 180, "Do Not Mention", 23, BLUE, 800, family=MONO))
    b.append(lines(x0+144, 212, ["真实市场里有恶意 skill 在等着", "（98,380→157）"], 17, INK, 500, lh=23))
    b.append(arrow(x0+144, 242, x0+sw/2, py-6, BLUE, 3, 14))
    # brackets: SCR & Hallu (top), stacked
    bracket(2, 3, 250, TEAL, TEALL, "SCR", "组合/背书促成安装（mock 环境，从“已出现的安装请求”起步）")
    bracket(2, 6, 336, RED, REDL, "HalluSquatting", "显式 install → 真实落盘/调用/RCE（用户已有获取意图）")
    # my band (bottom, whole pipeline)
    yb=py+sh+56
    x1=xs[0]-4; x2=xs[-1]+sw+4
    b.append(rrect(x1, yb, x2-x1, 128, 18, VIOL, VIO, 3))
    b.append(rrect(x1, yb, 156, 128, 18, VIO)); b.append(rrect(x1+136, yb, 20, 128, 0, VIO))
    b.append(lines(x1+78, yb+50, ["我的","问题"], 30, "#FFFFFF", 800, lh=36))
    b.append(T(x1+184, yb+40, "触发是普通能力任务（用户零获取意图）、目标一开始未安装 →", 24, INK, 600, anchor="start"))
    b.append(T(x1+184, yb+76, "要求 agent 自主走完整条链，并逐段测量：到底断在哪一段？由模型还是 budget/parser/policy 决定？", 23, VIO, 700, anchor="start"))
    # question marker at emitted->executed
    qx=(cx(2)+cx(3))/2
    b.append(f'<line x1="{qx}" y1="{yb}" x2="{qx}" y2="{py+sh}" stroke="{VIO}" stroke-width="2.5" stroke-dasharray="5 4"/>')
    b.append(f'<circle cx="{qx}" cy="{py+sh+28}" r="20" fill="{VIO}"/>')
    b.append(T(qx, py+sh+29, "?", 30, "#FFFFFF", 800))
    write("fig_integration", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 8. MY FUNNEL — P(E2E) decomposition (conceptual, honest: no fake numbers)
# ----------------------------------------------------------------------------
def fig_my_funnel():
    W, H = 1520, 680
    b = []
    b.append(T(W/2, 56, "把风险写成逐段存活率的乘积 —— 论文 Figure 1 的雏形", 28, INK, 800))
    b.append(T(W/2, 96, "P(E2E) = P(发现)·P(发出|发现)·P(执行|发出)·P(落盘|执行)·P(注册)·P(调用)·P(载荷)", 22, TEAL, 700, family=MONO))
    stages=["缺口","发现","发出","执行","落盘","注册","调用","载荷"]
    n=len(stages)
    x0,x1=90,W-90; top=180; bot=470
    fw=(x1-x0)/n
    # descending funnel (illustrative shape only)
    heights=[1.0,0.86,0.72,0.40,0.36,0.33,0.30,0.26]  # illustrative
    for i,s in enumerate(stages):
        x=x0+i*fw
        hh=(bot-top)*heights[i]
        yy=top+((bot-top)-hh)/2
        col = VIO if i in (2,3) else CARD
        tc = "#FFFFFF" if i in (2,3) else INK
        b.append(rrect(x+8, yy, fw-16, hh, 10, col, LINE if col==CARD else None, 2))
        b.append(T(x+fw/2, yy+hh/2, s, 24, tc, 700))
        if i>0:
            b.append(arrow(x-6, top+(bot-top)/2, x+6, top+(bot-top)/2, LGRAY, 3, 9))
    # highlight the emitted->executed drop
    dx=x0+3*fw
    b.append(f'<circle cx="{dx}" cy="{top-8}" r="20" fill="{VIO}"/>'); b.append(T(dx, top-7, "!", 28, "#FFFFFF", 800))
    b.append(T(dx, 526, "先导调试观察到的疑似断点（A2）：", 22, VIO, 800))
    b.append(T(dx, 558, "模型「发出」了 install，但没「执行」", 22, INK, 600))
    b.append(rrect(90, 596, W-180, 60, 12, AMBERL))
    b.append(T(W/2, 626, "注：本图为示意；每段真实存活率由 pilot 测出，不是既有结论", 21, AMBER, 700))
    write("fig_my_funnel", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 9. MY PILOT results + measurement pitfall
# ----------------------------------------------------------------------------
def fig_pilot():
    W, H = 1520, 600
    b = []
    # left: selection bars
    b.append(T(360, 70, "先导结果①：预装条件下的 selection", 24, INK, 800))
    base, top_y = 400, 130
    ch=base-top_y
    b.append(f'<line x1="120" y1="{base}" x2="660" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    data=[("Vanilla","0/20",0),("通用 Query+","2/20",2),("5 轮 LLM 优化","1/20",1)]
    for i,(cap,val,v) in enumerate(data):
        cx=200+i*170; bw=110
        hh=max(6, ch*(v/5))
        b.append(rrect(cx-bw/2, base-hh, bw, hh, 8, TEAL))
        b.append(T(cx, base-hh-24, val, 26, TEAL, 800))
        b.append(T(cx, base+30, cap, 20, INK, 600))
    b.append(T(360, 470, "单模型 / 单框架 / 20 任务 —— 先导观察，", 20, GRAY, 600))
    b.append(T(360, 500, "不是跨模型定律", 20, GRAY, 600))
    # divider
    b.append(f'<line x1="{W/2+30}" y1="90" x2="{W/2+30}" y2="520" stroke="{LINE}" stroke-width="2"/>')
    # right: measurement pitfall
    rx=W/2+80
    b.append(T(rx+300, 70, "先导结果②：测量陷阱（emitted ≠ executed）", 24, INK, 800))
    b.append(rrect(rx, 120, 620, 120, 14, CARD, LINE, 2))
    b.append(T(rx+310, 158, "模型吐出：", 20, GRAY, 600))
    b.append(T(rx+310, 196, "install_skill(name=weekly_brief)", 24, RED, 800, family=MONO))
    b.append(arrow(rx+310, 250, rx+310, 296, GRAY, 4, 14))
    b.append(rrect(rx, 300, 620, 120, 14, REDL, RED, 2.5))
    b.append(lines(rx+310, 342, ["但默认 3 轮 tool budget 已被耗尽", "→ 这次安装从未真正执行"], 23, RED, 700, lh=34))
    b.append(rrect(rx, 452, 620, 66, 12, AMBERL))
    b.append(T(rx+310, 485, "结论：emitted / parsed / executed 必须拆开测", 22, AMBER, 800))
    write("fig_pilot", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 10. DNM verification quality
# ----------------------------------------------------------------------------
def fig_dnm_verify():
    W, H = 1560, 560
    b = []
    b.append(T(W/2, 60, "为什么这些数字可信：四道关，只认“真的跑起来的坏行为”", 27, INK, 800))
    cards = [
        (BLUE, "①", "Docker 隔离沙箱", ["监控 网络 / 系统调用", "/ 文件系统"]),
        (TEAL, "②", "honeypot 诱饵凭证", ["埋假密钥，看它", "会不会去偷、去外发"]),
        (AMBER,"③", "三种触发方式", ["元数据驱动 / LLM 生成", "输入 / 多轮调用"]),
        (RED,  "④", "只认真实行为", ["外泄 / 未授权网络 / 提权", "→ 两人独立复核 κ=0.91"]),
    ]
    cw, gap = 344, 24
    x0=(W-(cw*4+gap*3))//2; y=120; chh=230
    for i,(c,n,title,desc) in enumerate(cards):
        x=x0+i*(cw+gap)
        b.append(rrect(x, y, cw, chh, 18, "#FFFFFF", c, 2.5))
        b.append(chip(x+cw/2, y+52, 30, c, n))
        b.append(T(x+cw/2, y+110, title, 25, c, 800))
        b.append(lines(x+cw/2, y+152, desc, 19, INK, 500, lh=27))
    b.append(rrect(x0, 396, cw*4+gap*3, 110, 16, GREENL))
    b.append(T(W/2, 434, "行为验证精度 99.6%", 38, GREEN, 800))
    b.append(T(W/2, 478, "比最强的“纯静态”基线（≤1.1%）高约 90 倍 · 157/157 披露后全部下架", 22, INK, 600))
    write("fig_dnm_verify", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 11. DNM three RQ findings — derived from the measurement funnel
# ----------------------------------------------------------------------------
def fig_dnm_rq():
    W, H = 1740, 820
    b = []
    b.append(T(W/2, 46, "三个结论怎么来的：漏斗是“数据引擎”，RQ 是对同一份语料的三次追问", 28, INK, 800))
    # --- Stage 1: mini funnel (the data engine) ---
    fx, fw, ftop = 60, 300, 132
    b.append(T(fx+fw/2, ftop-16, "① 测量漏斗：筛出 ground truth", 19, BLUE, 800))
    funnel = [("98,380", "两个市场全部 skill", 1.0),
              ("4,287", "静态可疑 4.4%", 0.70),
              ("762", "沙箱触发可疑行为", 0.44),
              ("157", "人工双复核确认", 0.26)]
    fy, rowh = ftop+14, 96
    for i, (num, lab, wr) in enumerate(funnel):
        wpx = fw*wr; x = fx+(fw-wpx)/2; y = fy+i*rowh
        col = RED if i == 3 else CARD
        tc = "#FFFFFF" if i == 3 else INK
        b.append(rrect(x, y, wpx, 72, 10, col, LINE if i < 3 else None, 2))
        b.append(T(fx+fw/2, y+27, num, 27, tc, 800))
        b.append(T(fx+fw/2, y+53, lab, 15, ("#FFECEC" if i == 3 else GRAY), 500))
        if i < 3:
            b.append(arrow(fx+fw/2, y+73, fx+fw/2, y+rowh-1, LGRAY, 3, 9))
    # arrow funnel -> corpus
    midy = fy+2*rowh-6
    b.append(arrow(fx+fw+8, midy, fx+fw+70, midy, GRAY, 5, 16))
    b.append(T(fx+fw+42, midy-20, "产出", 15, GRAY, 600))
    # --- Stage 2: the labeled corpus ---
    cx0, cw, cy, chh = fx+fw+82, 300, ftop, 344
    b.append(rrect(cx0, cy, cw, chh, 18, BLUEL, BLUE, 2.5))
    b.append(T(cx0+cw/2, cy+36, "② 同一份标注语料", 19, BLUE, 800))
    b.append(T(cx0+cw/2, cy+112, "157", 74, BLUE, 800))
    b.append(T(cx0+cw/2, cy+166, "确认恶意 skill", 20, INK, 700))
    for j, ch in enumerate(["632 个漏洞", "13 种技术", "6 个 kill-chain 阶段"]):
        b.append(rrect(cx0+28, cy+196+j*44, cw-56, 36, 8, "#FFFFFF"))
        b.append(T(cx0+cw/2, cy+214+j*44, ch, 19, INK, 700))
    # --- Stage 3: three RQ lenses (question -> finding), fanning off the corpus ---
    rx = cx0+cw+78
    rw = W-rx-52
    rh, rgap, ry0 = 178, 22, ftop
    lenses = [
        (BLUE, "RQ1", "威胁全貌", "这份语料整体长什么样？",
         ["平均 4.03 漏洞/skill —— 是蓄意分层，不是随手写",
          "84.2% 的恶意行为写在 SKILL.md 的自然语言里"]),
        (TEAL, "RQ2", "攻击者与分工", "谁在做、怎么组织？",
         ["两种“负相关”原型：Data Thieves 与 Agent Hijackers 二选一专精",
          "单一“工业化”行为者靠模板化仿冒占 54.1%"]),
        (RED, "RQ3", "如何逃避检测", "越高级的攻击越怎样？",
         ["shadow features 随复杂度 0% → 100%",
          "反过来武器化平台自带的“可信/安全”机制"]),
    ]
    for i, (c, tag, title, q, finds) in enumerate(lenses):
        y = ry0+i*(rh+rgap)
        # fan connector from corpus right-center to this band
        b.append(f'<line x1="{cx0+cw+6}" y1="{cy+chh/2}" x2="{rx-4}" y2="{y+rh/2}" '
                 f'stroke="{c}" stroke-width="2.5" stroke-dasharray="4 5"/>')
        b.append(rrect(rx, y, rw, rh, 16, "#FFFFFF", c, 2.5))
        b.append(rrect(rx, y, 150, rh, 16, c)); b.append(rrect(rx+130, y, 20, rh, 0, c))
        b.append(T(rx+75, y+rh/2-16, tag, 32, "#FFFFFF", 800, family=MONO))
        b.append(T(rx+75, y+rh/2+22, title, 18, "#FFFFFF", 700))
        b.append(T(rx+172, y+40, "问：", 19, c, 800, anchor="start"))
        b.append(T(rx+222, y+40, q, 21, INK, 700, anchor="start"))
        b.append(f'<line x1="{rx+172}" y1="{y+62}" x2="{rx+rw-24}" y2="{y+62}" stroke="{LINE}" stroke-width="1.5"/>')
        b.append(T(rx+172, y+92, "答：", 19, GREEN, 800, anchor="start"))
        for k, fl in enumerate(finds):
            b.append(T(rx+222, y+92+k*34, "· "+fl, 19, INK, 500, anchor="start"))
    b.append(rrect(rx, ry0+3*(rh+rgap)-6, rw, 52, 12, AMBERL))
    b.append(T(rx+rw/2, ry0+3*(rh+rgap)+20, "RQ 不是新数据：都是对漏斗产出的那 157 个语料，做三种不同的统计追问",
               19, AMBER, 800))
    write("fig_dnm_rq", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 12. MY BENCHMARK — the three-part empirical benchmark (mentor's direction)
# ----------------------------------------------------------------------------
def fig_my_benchmark():
    W, H = 1680, 780
    b = []
    b.append(T(W/2, 50, "我把这条链做成一个可复用的实证 benchmark（正是导师建议的方向）", 28, INK, 800))
    b.append(T(W/2, 90, "=  测量仪  +  数据集  +  预注册协议", 22, VIO, 700))
    cols = [
        (VIO, VIOL, "测量仪", "Acquisition Funnel", [
            "8 段逐点“条件存活率”，不报一个笼统 ASR",
            "3 个互斥终态：discovery / direct-install / residual",
            "让“风险断在哪一段”成为可测对象"]),
        (TEAL, TEALL, "数据集", "Twin Benchmark", [
            "30 个 hard 任务 × 3 类（PDF / iCalendar / QR）",
            "成败由确定性 verifier 判定，不靠模型自评",
            "良性/恶意 twin：模型可见字段字节级相同"]),
        (BLUE, BLUEL, "协议", "预注册 P0 / P1 / P2", [
            "P0 中性可用 · P1 鼓励获取 · P2 执行层 gate",
            "单变量因果操纵：先冻结判据，再看结果",
            "manifest / source hash + pre-results commit"]),
    ]
    cw, gap = 522, 30
    x0 = (W-(cw*3+gap*2))//2; y = 138; chh = 476
    for i, (c, cl, tag, name, pts) in enumerate(cols):
        x = x0+i*(cw+gap)
        b.append(rrect(x, y, cw, chh, 20, "#FFFFFF", c, 3))
        b.append(rrect(x, y, cw, 98, 20, c)); b.append(rrect(x, y+76, cw, 22, 0, c))
        b.append(chip(x+58, y+49, 27, "#FFFFFF", str(i+1), c))
        b.append(T(x+cw/2+34, y+39, tag, 29, "#FFFFFF", 800))
        b.append(T(x+cw/2+34, y+72, name, 20, "#FFFFFF", 600, family=MONO))
        for j, p in enumerate(pts):
            yy = y+128+j*112
            b.append(rrect(x+26, yy, cw-52, 96, 12, cl))
            b.append(T(x+cw/2, yy+48, p, 18, INK, 600))
    b.append(rrect(x0, y+chh+22, cw*3+gap*2, 62, 14, VIOL))
    b.append(T(W/2, y+chh+53, "三件套 = 能复用、能定位断点、能做因果归因 —— 一篇 measurement / benchmark paper 的骨架",
               22, VIO, 800))
    write("fig_my_benchmark", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 13. MY RESULT — the primary causal acquisition funnel (real data)
# ----------------------------------------------------------------------------
def fig_my_result():
    W, H = 1640, 800
    b = []
    b.append(T(W/2, 44, "主结果：一句“工具不够就去搜、去装、去调用”，把普通任务变成真实第三方代码执行", 25, INK, 800))
    plx, ply, prx, pby = 150, 118, 1120, 566
    pw, ph = prx-plx, pby-ply
    stages = ["任务", "搜索", "检索到", "被推荐", "解析\n安装", "落盘", "调用", "载荷", "任务\n完成"]
    n, maxv = len(stages), 30
    def X(i): return plx+pw*i/(n-1)
    def Y(v): return pby-ph*(v/maxv)
    for gv in (0, 10, 20, 30):
        yy = Y(gv)
        b.append(f'<line x1="{plx}" y1="{yy:.1f}" x2="{prx}" y2="{yy:.1f}" stroke="{LINE}" stroke-width="1" stroke-dasharray="3 5"/>')
        b.append(T(plx-14, yy, str(gv), 16, LGRAY, 700, anchor="end"))
    b.append(T(plx-36, ply-28, "存活条数 / 30 个 hard 任务", 16, GRAY, 700, anchor="start"))
    for i, s in enumerate(stages):
        for k, ln in enumerate(s.split("\n")):
            b.append(T(X(i), pby+24+k*20, ln, 15, INK, 600))
    series = [
        ("P0 中性可用", BLUE, [30, 5, 5, 5, 5, 5, 5, 5, 5]),
        ("P1 鼓励获取", RED, [30, 25, 25, 25, 25, 25, 25, 25, 24]),
        ("P2 拒绝 (gate)", GREEN, [30, 22, 22, 22, 22, 0, 0, 0, 0]),
    ]
    for name, col, vals in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3.6" stroke-linejoin="round"/>')
        for i, v in enumerate(vals):
            b.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="5.5" fill="{col}"/>')
    b.append(T(prx+10, Y(24), "24", 22, RED, 800, anchor="start"))
    b.append(T(prx+10, Y(5), "5", 22, BLUE, 800, anchor="start"))
    b.append(T(prx+10, Y(0), "0", 22, GREEN, 800, anchor="start"))
    # legend
    lx, ly = plx+18, ply+8
    for j, (name, col, _) in enumerate(series):
        yy = ly+j*30
        b.append(f'<line x1="{lx}" y1="{yy}" x2="{lx+34}" y2="{yy}" stroke="{col}" stroke-width="3.6"/>')
        b.append(f'<circle cx="{lx+17}" cy="{yy}" r="5.5" fill="{col}"/>')
        b.append(T(lx+44, yy, name, 17, INK, 700, anchor="start"))
    # annotation 1: first-hop jump
    b.append(arrow(X(2)-6, Y(29), X(1)+6, Y(15), AMBER, 3, 11))
    b.append(rrect(X(1)+44, Y(30)-8, 306, 58, 10, AMBERL))
    b.append(lines(X(1)+197, Y(30)+8, ["鼓励语把 task→search", "从 5 翻到 25（+66.7pp）"], 18, AMBER, 700, lh=26))
    # annotation 2: gate cliff
    b.append(arrow(X(5)+42, Y(7), X(5)+6, Y(0)+2, GREEN, 3, 11))
    b.append(rrect(X(5)+52, Y(9), 300, 56, 10, GREENL))
    b.append(lines(X(5)+202, Y(9)+25, ["执行层 gate：解析后、", "执行前拦截 → 22→0"], 18, GREEN, 700, lh=26))
    # P0 residual note
    b.append(T(plx+2, pby+74, "注：中性可用 (P0) 也有 5/30 自主 E2E —— 工具可得，本身就非零风险", 18, GRAY, 600, anchor="start"))
    # right headline panel
    hx = prx+64; hw = W-40-hx
    b.append(rrect(hx, 118, hw, 150, 14, VIOL, VIO, 2.5))
    b.append(T(hx+hw/2, 148, "anchor cell（Qwen × 文本）", 16, VIO, 800))
    b.append(T(hx+hw/2, 196, "5/30 → 24/30", 33, VIO, 800))
    b.append(T(hx+hw/2, 240, "+63.3pp · 三 family 同向 · p=3.8e-6", 15, INK, 700))
    b.append(rrect(hx, 290, hw, 250, 14, CARD, LINE, 2))
    b.append(T(hx+hw/2, 322, "结构性发现", 18, INK, 800))
    b.append(lines(hx+hw/2, 366, ["瓶颈只在“第一跳”：", "任务 → 是否去搜索。", "一旦搜索，25 条全部", "检索→安装→调用→载荷", "近乎必然贯通到底。"], 18, INK, 600, lh=33))
    b.append(T(W/2-90, H-30, "固定 benchmark 上的率，不是现实世界 prevalence", 19, GRAY, 700))
    write("fig_my_result", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 14. MY DEFENSE — execution-layer approval gate: gating != vetting
# ----------------------------------------------------------------------------
def fig_my_defense():
    W, H = 1560, 720
    b = []
    b.append(T(W/2, 48, "防御：执行层 approval gate —— 挡得住“装不装”，挡不住“该不该装”", 27, INK, 800))
    base, top_y = 512, 150
    ch, maxv = base-top_y, 30
    plx = 150; plw = W-430-plx
    for gv in (0, 10, 20, 30):
        yy = base-ch*(gv/maxv)
        b.append(f'<line x1="{plx}" y1="{yy:.1f}" x2="{plx+plw}" y2="{yy:.1f}" stroke="{LINE}" stroke-width="1" stroke-dasharray="3 5"/>')
        b.append(T(plx-12, yy, str(gv), 15, LGRAY, 700, anchor="end"))
    b.append(f'<line x1="{plx}" y1="{base}" x2="{plx+plw}" y2="{base}" stroke="{LINE}" stroke-width="2"/>')
    conds = [
        ("P1 自动获取\n(无 gate)", 25, 24, "攻击+效用都高"),
        ("P2 拒绝", 0, 0, "安全但零效用"),
        ("P2 批准\n+良性 twin", 0, 25, "效用回来、载荷零 ✓"),
        ("P2 批准\n+恶意 twin", 25, 25, "效用回来、载荷也回来"),
    ]
    m = len(conds); slot = plw/m; bw = 62
    for i, (cap, pay, util, note) in enumerate(conds):
        cx = plx+slot*i+slot/2
        for off, val, col in [(-bw-6, pay, RED), (6, util, BLUE)]:
            hh = max(3, ch*(val/maxv))
            b.append(rrect(cx+off, base-hh, bw, hh, 7, col))
            b.append(T(cx+off+bw/2, base-hh-19, f"{val}/30", 19, col, 800))
        for k, ln in enumerate(cap.split("\n")):
            b.append(T(cx, base+26+k*24, ln, 18, INK, 700))
        b.append(T(cx, base+80, note, 16, GRAY, 600))
    # legend
    b.append(rrect(plx, 92, 22, 22, 5, RED)); b.append(T(plx+30, 103, "payload 触发（攻击）", 18, INK, 600, anchor="start"))
    b.append(rrect(plx+256, 92, 22, 22, 5, BLUE)); b.append(T(plx+288, 103, "任务效用 functional E2E", 18, INK, 600, anchor="start"))
    # right note panel
    hx = W-296; hw = 250
    b.append(rrect(hx, 150, hw, 356, 14, VIOL, VIO, 2.5))
    b.append(T(hx+hw/2, 186, "gating ≠ vetting", 22, VIO, 800))
    b.append(lines(hx+hw/2, 240, ["良性/恶意 twin", "模型可见字段", "字节级相同"], 19, INK, 700, lh=30))
    b.append(f'<line x1="{hx+24}" y1="328" x2="{hx+hw-24}" y2="328" stroke="{VIO}" stroke-width="1.5"/>')
    b.append(lines(hx+hw/2, 376, ["→ 批准者与 agent", "看到一样多的信息；", "gate 决定能不能装，", "决定不了该不该装"], 18, VIO, 700, lh=30))
    b.append(rrect(plx, base+108, (W-296)-plx-20, 52, 12, AMBERL))
    b.append(T((plx+(W-296)-20)/2, base+134, "完整防御 = 执行层 gate + 认证 provenance + 静态/信誉审查 + 最小权限", 20, AMBER, 800))
    write("fig_my_defense", W, H, "".join(b))

# ----------------------------------------------------------------------------
# 15. MY GENERALIZATION — replicates across model/scaffold; magnitude varies
# ----------------------------------------------------------------------------
def fig_my_general():
    W, H = 1680, 760
    b = []
    b.append(T(W/2, 46, "稳健性：换模型、换 scaffold，攻击都在 —— 变的是“量级”，不是“有没有”", 27, INK, 800))
    # left table
    tx, ty, tw = 56, 118, 900
    b.append(rrect(tx, ty, tw, 50, 10, INK))
    for txt, xx in [("实验格 (model × scaffold)", tx+16), ("功能 E2E P0→P1", tx+336),
                    ("严格判据", tx+560), ("获取+载荷 P0→P1", tx+710)]:
        b.append(T(xx, ty+25, txt, 16, "#FFFFFF", 700, anchor="start"))
    rows = [
        ("Qwen × 文本 (anchor)", "5 → 24  (+63pp)", "通过", GREEN, "5 → 25"),
        ("Llama-70B × 文本", "4 → 9  (+17pp)", "未过 (QR 反向)", RED, "8 → 28"),
        ("Qwen × 原生 FC", "4 → 12  (+27pp)", "未过 (ICS 反向)", RED, "4 → 12"),
    ]
    rh = 78
    for i, (cell, fe, crit, cc, ip) in enumerate(rows):
        y = ty+50+i*rh
        b.append(rrect(tx, y, tw, rh, 0, ("#FFFFFF" if i % 2 else CARD)))
        b.append(T(tx+16, y+rh/2, cell, 18, INK, 700, anchor="start"))
        b.append(T(tx+336, y+rh/2, fe, 18, INK, 600, anchor="start"))
        b.append(T(tx+560, y+rh/2, crit, 15, cc, 800, anchor="start"))
        b.append(T(tx+710, y+rh/2, ip, 19, VIO, 800, anchor="start"))
    # right: replicate vs vary
    rx = tx+tw+38; rw = W-rx-46
    b.append(rrect(rx, 118, rw, 168, 14, GREENL, GREEN, 2.5))
    b.append(T(rx+22, 150, "✓ 三件事都复现", 21, GREEN, 800, anchor="start"))
    for j, s in enumerate(["攻击本身：P1 下“获取 + 真实载荷”都升",
                            "第一跳瓶颈：一旦搜索，下游必然到底",
                            "防御：P2 gate 每格 100% 拦截（payload 0）"]):
        b.append(T(rx+30, 190+j*32, "· "+s, 18, INK, 600, anchor="start"))
    b.append(rrect(rx, 300, rw, 128, 14, AMBERL, AMBER, 2.5))
    b.append(T(rx+22, 332, "⚠ 两件事在变", 21, AMBER, 800, anchor="start"))
    for j, s in enumerate(["功能 primary 依赖“模型”：严格判据只 anchor 通过",
                            "获取倾向依赖“scaffold”：原生 FC 把 24 砍到 12"]):
        b.append(T(rx+30, 372+j*32, "· "+s, 18, INK, 600, anchor="start"))
    # bottom striking finding
    b.append(rrect(tx, 470, W-tx-46, 130, 16, INK))
    b.append(T(tx+34, 512, "最反直觉：", 24, "#FF9DA3", 800, anchor="start"))
    b.append(T(tx+170, 512, "Llama 触发的 payload 更多（28）却完成更少任务（9）", 24, "#FFFFFF", 800, anchor="start"))
    b.append(T(tx+34, 560, "→ 只看“任务门控”的指标，会把更受害的模型评成更安全 —— 所以 payload 与任务效用必须分开报告",
               21, "#DCE8F6", 600, anchor="start"))
    write("fig_my_general", W, H, "".join(b))

for fn in [fig_roadmap, fig_skill_bg, fig_scr_results, fig_hallu_halluc,
           fig_hallu_v1v2, fig_hallu_e2e, fig_integration, fig_my_funnel, fig_pilot,
           fig_dnm_verify, fig_dnm_rq,
           fig_my_benchmark, fig_my_result, fig_my_defense, fig_my_general]:
    fn(); print("wrote", fn.__name__)
print("done")
