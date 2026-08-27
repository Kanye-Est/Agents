#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate custom slide figures as SVG (rendered to PNG by rsvg-convert).
Design system: clean, few words, big numbers — matches an image-first talk.
All numbers are source-verified (see idea/27 & idea/28 原文核对 blocks)."""
import math, os, html

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS, exist_ok=True)

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
# 11. DNM three RQ findings
# ----------------------------------------------------------------------------
def fig_dnm_rq():
    W, H = 1600, 620
    b = []
    b.append(T(W/2, 56, "论文的重点在后半段：三个研究问题", 27, INK, 800))
    cards = [
        (BLUE, BLUEL, "RQ1", "威胁全貌", [
            "632 个漏洞 · 13 种技术 · 6 阶段",
            "平均 4.03 个 —— 蓄意分层",
            "84.2% 写在 SKILL.md 文字里"]),
        (TEAL, TEALL, "RQ2", "攻击策略", [
            "两种“负相关”原型：",
            "Data Thieves（外泄）",
            "vs Agent Hijackers（劫持）",
            "单一行为者占 54.1%"]),
        (RED, REDL, "RQ3", "如何逃避", [
            "逃避随复杂度升级：",
            "shadow features 0% → 100%",
            "武器化平台自带的信任机制"]),
    ]
    cw, gap = 490, 40
    x0=(W-(cw*3+gap*2))//2; y=110; chh=430
    for i,(c,cl,rq,title,desc) in enumerate(cards):
        x=x0+i*(cw+gap)
        b.append(rrect(x, y, cw, chh, 20, "#FFFFFF", c, 3))
        b.append(rrect(x, y, cw, 74, 20, c)); b.append(rrect(x, y+52, cw, 22, 0, c))
        b.append(T(x+90, y+37, rq, 30, "#FFFFFF", 800, family=MONO))
        b.append(T(x+cw/2+40, y+37, title, 28, "#FFFFFF", 700))
        for j,d in enumerate(desc):
            b.append(T(x+34, y+128+j*52, "· "+d, 22, INK, 600, anchor="start"))
    write("fig_dnm_rq", W, H, "".join(b))

for fn in [fig_roadmap, fig_skill_bg, fig_scr_results, fig_hallu_halluc,
           fig_hallu_v1v2, fig_hallu_e2e, fig_integration, fig_my_funnel, fig_pilot,
           fig_dnm_verify, fig_dnm_rq]:
    fn(); print("wrote", fn.__name__)
print("done")
