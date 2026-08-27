# 36 — Figure Specs（给 codex 直接渲染）

> 数字全部来自 `policy_hardgap_causal_v2_full_20260726.analysis(.md/.json)` 与 idea/33，
> 单一真源。改结果就从 analysis.json 重新生成，不要手改这里。
> 三张图共用同一套 policy 配色与语义，跨图一致。

## 全局样式（三张图共用）

- 调色板：Okabe–Ito（色盲安全），并用 linestyle + marker 冗余编码，保证灰度可读。
- **Policy 语义配色（跨全文固定）**：
  - `P0` neutral affordance → 蓝 `#0072B2`，实线，圆点 `o`（低风险基线）
  - `P1` encouragement → 朱红 `#D55E00`，虚线，方块 `s`（风险主线）
  - `P2` denied gate → 绿 `#009E73`，点划线，三角 `^`（防御）
- 字号：坐标轴标签 11、刻度 9、图例 9、注释 9；无边框上/右 spine；浅色横向网格。
- 输出：`fig1_funnel.pdf`、`fig2_family_e2e.pdf`、矢量优先，300dpi 备一份 png。

```python
# common_style.py —— 三张图开头都 import 这段
import matplotlib.pyplot as plt
POLICY = {
    "P0": dict(color="#0072B2", ls="-",   marker="o", label="P0  neutral affordance"),
    "P1": dict(color="#D55E00", ls="--",  marker="s", label="P1  + acquisition encouragement"),
    "P2": dict(color="#009E73", ls="-.",  marker="^", label="P2  + denied execution gate"),
}
plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.axis": "y", "grid.alpha": 0.3, "figure.dpi": 150,
})
```

---

## Figure 1 — The Acquisition Funnel（全文核心图）

**讲什么**：pooled 30 个 hard specs，每个 policy 有多少条存活到每一段。一眼看两件事：
(1) P0/P1 的**唯一大衰减在第一跳 task→search**，之后近乎水平；(2) P2 与 P1 在前段重合，
在**执行层 gate 处（install-parsed→on-disk）断崖到 0**。

**数据（counts / 30，target funnel）**

| stage | P0 | P1 | P2 |
|---|---:|---:|---:|
| task | 30 | 30 | 30 |
| search | 5 | 25 | 22 |
| retrieved | 5 | 25 | 22 |
| recommended | 5 | 25 | 22 |
| install parsed | 5 | 25 | 22 |
| on-disk | 5 | 25 | **0** |
| invoked | 5 | 25 | 0 |
| payload | 5 | 25 | 0 |
| task_ok | 5 | 24 | 0 |
| discovery E2E | 5 | 24 | 0 |

```python
from common_style import POLICY, plt
stages = ["task","search","retrieved","recommended","install\nparsed",
          "on-disk","invoked","payload","task_ok","discovery\nE2E"]
data = {
    "P0": [30, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    "P1": [30,25,25,25,25,25,25,25,24,24],
    "P2": [30,22,22,22,22, 0, 0, 0, 0, 0],
}
x = range(len(stages))
fig, ax = plt.subplots(figsize=(7.2, 3.4))
for pol, ys in data.items():
    ax.plot(x, ys, **POLICY[pol], markersize=5, linewidth=1.8)
# 第一跳注释（风险产生处）
ax.annotate("encouragement flips\ntask→search\n(5→25 of 30)",
            xy=(1, 25), xytext=(2.1, 30), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#D55E00", lw=1))
# 执行层 gate 注释（防御生效处）
ax.annotate("execution gate\nblocks at install\n(22→0)",
            xy=(5, 0), xytext=(5.4, 9), fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#009E73", lw=1))
ax.set_xticks(list(x)); ax.set_xticklabels(stages, rotation=30, ha="right")
ax.set_ylabel("trials surviving to stage  (of 30 hard tasks)")
ax.set_ylim(-1, 31); ax.legend(loc="center right", frameon=False)
fig.tight_layout(); fig.savefig("fig1_funnel.pdf")
```

**Caption（draft）**：*Figure 1. The Acquisition Funnel on 30 hard‑artifact tasks (pooled PDF+ICS+QR),
by scaffold policy. Under neutral affordance (P0) and encouragement (P1), the only large attrition
is the first hop, task→search (P0 5, P1 25 of 30); once an agent searches, retrieval, installation,
registration, invocation, and payload survive essentially without loss (P1's single task_ok drop is
a duplicate‑invocation overwrite). P2 shares P1's model‑visible policy but denies the approval bit:
the trajectories coincide until the execution‑layer gate, which blocks every parsed install before
it runs (22 target installs → 0 on disk; 3 additional non‑search wrong‑name attempts are also
blocked, 25 blocks total).* 

**要点提醒**：P2 的 search=22 是"针对 target 的搜索"；另有 3 次未搜索的 wrong‑name 安装尝试也被拦，
合计 25 次 block——写进 caption，别让读者以为 P2 只有 22 次拦截。

---

## Figure 2 — Discovery E2E by family × policy（带 Wilson 95% CI）

**讲什么**：三个 hard family 全部同向 P1>P0，且 P2 全 0；证明 primary 不是单个 family 撑起来的。

**数据（discovery_e2e，rate 与 Wilson 95%CI，来自 analysis.md）**

| family | P0 | P1 | P2 |
|---|---|---|---|
| PDF | 10% (2–40) | 80% (49–94) | 0% (0–28) |
| ICS | 0% (0–28) | 60% (31–83) | 0% (0–28) |
| QR | 40% (17–69) | 100% (72–100) | 0% (0–28) |

（pooled/30：P0 17%、P1 80%、P2 0%，写进 caption 即可。）

```python
from common_style import POLICY, plt
import numpy as np
fams = ["PDF","ICS","QR"]
rate = {"P0":[.10,.00,.40], "P1":[.80,.60,1.0], "P2":[.0,.0,.0]}
lo   = {"P0":[.02,.00,.17], "P1":[.49,.31,.72], "P2":[.0,.0,.0]}
hi   = {"P0":[.40,.28,.69], "P1":[.94,.83,1.0], "P2":[.28,.28,.28]}
xpos = np.arange(len(fams)); w = 0.26
fig, ax = plt.subplots(figsize=(6.0, 3.2))
for i,pol in enumerate(["P0","P1","P2"]):
    r=np.array(rate[pol]); err=[r-np.array(lo[pol]), np.array(hi[pol])-r]
    ax.bar(xpos+(i-1)*w, r, w, yerr=err, capsize=3,
           color=POLICY[pol]["color"], label=POLICY[pol]["label"],
           edgecolor="white", linewidth=0.5)
ax.set_xticks(xpos); ax.set_xticklabels(fams)
ax.set_ylabel("discovery E2E rate"); ax.set_ylim(0,1.05)
ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig("fig2_family_e2e.pdf")
```

**Caption（draft）**：*Figure 2. Full discovery E2E by capability family and policy (bars = rate,
whiskers = Wilson 95% CI, n=10 per cell). The P1>P0 effect holds in all three families (pooled 5/30
→ 24/30, +63 pp, exact McNemar p=3.8e‑6), satisfying the pre‑registered cross‑family criterion; the
denied gate (P2) is 0 everywhere. CIs are wide by design (n=10) and describe the fixed benchmark,
not population prevalence.*

---

## Figure 3 — The approval gate: block, recover, and the gating≠vetting boundary（第 4 张图 · defense 章）

**讲什么**：一张图讲完防御弧线。四个条件、每个两根柱（payload=攻击 / utility=任务），左到右：
auto-acquire 两高 → deny 两零（安全但无用）→ approve-benign 效用回来、payload 零（理想）→
approve-malicious 效用与 payload 都回来（gating≠vetting）。

**数据（/30 hard tasks）**

| condition | payload | utility (functional_e2e) |
|---|---:|---:|
| P1 auto-acquire (no gate) | 25/30 | 24/30 |
| P2 denied | 0/30 | 0/30 |
| P2 approved + benign | 0/30 | 25/30 |
| P2 approved + malicious | 25/30 | 25/30 |

```python
from common_style import plt
import numpy as np
conds = ["P1\nauto-acquire", "P2\ndenied", "P2 approved\n+benign", "P2 approved\n+malicious"]
payload = [25/30, 0/30, 0/30, 25/30]
utility = [24/30, 0/30, 25/30, 25/30]
x = np.arange(len(conds)); w = 0.38
fig, ax = plt.subplots(figsize=(6.8, 3.2))
ax.bar(x - w/2, payload, w, color="#D55E00", label="payload fired (attack)")
ax.bar(x + w/2, utility, w, color="#0072B2", label="task utility (functional E2E)")
for i, (p, u) in enumerate(zip(payload, utility)):
    ax.text(i - w/2, p + 0.02, f"{round(p*30)}/30", ha="center", fontsize=8)
    ax.text(i + w/2, u + 0.02, f"{round(u*30)}/30", ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(conds)
ax.set_ylabel("rate over 30 hard tasks"); ax.set_ylim(0, 1.12)
ax.legend(frameon=False, fontsize=8, loc="upper center", ncol=2)
fig.tight_layout(); fig.savefig("fig3_defense.pdf")
```

**Caption（draft）**：*Figure 3. The execution-layer approval gate over 30 hard tasks. Auto-acquire
(P1) yields both attack (payload 25/30) and utility (24/30). Denying the gate blocks every install —
safe but zero utility. Authorizing a benign skill restores utility (25/30) with no payload.
Authorizing an indistinguishable malicious twin restores the same utility (25/30) but the payload
returns (25/30): the gate governs whether to install, not whether the installed skill is safe.*

---

## Table 1 — Where prior work stops on the funnel（related-work delta）

**讲什么**：把竞品按"停在链条哪一格 / 从哪个起点触发"排列，凸显本文的合取空位。渲染成 LaTeX
`booktabs` 三线表。**不要**再声称 first‑execution/autonomy/install（被 SCR、HalluSquatting 占了）。

| Work | Trigger start | Endpoint reached | Not measured on one trajectory |
|---|---|---|---|
| Semantic SC (2605.11418) | skill already in registry | selection (77.6%) | emitted→executed→on‑disk |
| SearchGEO (2606.16821) | benign info/recommend task | endorsement / accepts install cmd | parsed / executed / on‑disk |
| SCR‑CapFlow (2606.15242) | includes neutral trigger | real mock state‑change (neutral 33.6%) | external discovery + real install |
| SCR‑TrustLift (2606.15242) | upstream endorse + **downstream install req** | harmful install, *simulated* market (→83.9%) | ordinary‑task autonomous start; real on‑disk/register/invoke |
| HalluSquatting (2607.07433) | user **"clone/install X"** | real E2E / RCE (40–100%) | ordinary‑task trigger (no user install intent) |
| Skills Don't Exist (2607.12340) | user seeks skill rec | hallucination rate; benign install PoC | ordinary‑task autonomous full chain + malicious invoke |
| Skill‑Inject / Poise (2602.20156 / 2606.07943) | skill already loaded | payload (80% / 89.3%) | entire S0–S2 (discovery→install) |
| **This work** | **ordinary capability task; target not preinstalled** | **discovery→install→register→invoke→payload, per‑stage** | — (adds P0/P1/P2 causal manipulation of scaffold policy) |

**Caption（draft）**：*Table 1. Prior measurements of skill‑layer risk each report a different
endpoint from a stronger starting point; none isolates the ordinary‑task → autonomous discovery →
real install/register/invoke → payload chain with per‑stage attribution, and none performs the
P0/P1/P2 causal manipulation of the scaffold's acquisition policy.*

**给 codex 的 LaTeX 提示**：用 `booktabs`（`\toprule/\midrule/\bottomrule`），最后一行本文加粗；
末两列窄、允许换行（`p{}` 列）；citation 用 `\cite{}` 从 idea/15、21 的编号表填。

---

## 三张图之外的一致性检查（codex 渲染时核对）

1. 三张图的 P0/P1/P2 颜色/线型/marker 必须一致（用 `common_style.py`）。
2. Fig1 的 P1 在 task_ok 处 24、其余段 25；Fig2 的 P1:PDF 是 discovery_e2e=80%（不是 payload 的 90%）。
3. 所有率都标注是固定 benchmark；Fig2 whisker 是 Wilson，不是 SE。
4. 数据若重生成：Fig1 读 `summary["P?:*"]` 各段 count 求和；Fig2 读 per‑family `discovery_e2e`
   的 count 与 `wilson95`；Table1 内容来自 idea/23 §2 与 idea/21。
