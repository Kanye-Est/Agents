# slides/ — 组会汇报材料（Do Not Mention 主讲 + SCR / HalluSquatting 补充 → 我的 idea）

**生成日期**：2026-07-29 · 图片优先、文字少、**27 页**、约 28–30 分钟 · 汇报人 Kan Shiyu。

## 直接用的文件
- **`组会_Do_Not_Mention_三篇.pptx`** — 可编辑 PPT（17 张图内嵌，含逐页演讲备注）。
- **`组会_Do_Not_Mention_三篇_预览.pdf`** — 可直接放映的预览，由 LibreOffice 直接渲染 `.pptx` 生成，与 PPT 逐页一致、CJK 字体已内嵌。
- **`演讲稿_SPEECH.md`** — 逐页口述稿 + 时间分配表（≤30 分钟）。

## 结构（4 段 + 我的工作）
每个论文分节的封面都带一个**「体裁 GENRE」徽标**，一眼区分：
- Do Not Mention＝**in-the-wild 大规模测量研究（不是 benchmark）**
- SCR＝受控实证 benchmark（SCR-Bench，mock 沙箱）
- HalluSquatting＝测量 + 真实产品端到端攻击
- **我的 idea＝受控实证 benchmark（导师建议的方向）**

## 图片来源（`figures/`）
- **截自原论文（4 张）**：`dnm_fig1_shadow`、`dnm_fig3_funnel`、`scr_fig1_chain`、`hallu_fig1_threat`。
- **自绘（13 张用于成片）**：roadmap / skill 背景 / 验证质量 / **RQ 由来（漏斗→语料→三追问）** /
  SCR 结果 / 幻觉率 / V1-V2 / E2E RCE / **整合中心图** /
  **MY WORK 四图**：`fig_my_benchmark`（三件套）、`fig_my_result`（P0 5→P1 24 主结果）、
  `fig_my_defense`（gating≠vetting）、`fig_my_general`（跨模型/scaffold 稳健性）。
- 旧的 `fig_my_funnel`（示意漏斗）与 `fig_pilot`（0/2/1 先导）**已不再进片**——被 v2 真实因果结果取代，
  脚本仍能生成但成片未引用。数字均与 `../33`/`../36`/`../40`/`../41` 的 analysis 单一真源一致。

## 重新生成（改字/改色/改数据后）
```bash
cd slides
.venv/bin/python make_figures.py      # 自绘图 SVG -> figures/*.png（改数据在此文件，用 rsvg-convert -z 2 渲染）
.venv/bin/python build_deck.py        # 生成 .pptx（改文案/顺序/体裁徽标在此文件）
.venv/bin/python preview_svg.py       # 用 LibreOffice 把 .pptx 渲染成预览 .pdf（忠实还原，不会漂移）
```
- 环境：`uv venv --python 3.12 .venv` + `uv pip install python-pptx Pillow`；渲染用系统 `rsvg-convert`、`libreoffice`。
- 字体：中文用 **Alibaba PuHuiTi 3.0**（本机已装），等宽用 JetBrains Maple Mono。

## 说明
- 预览 PDF 现由 **LibreOffice 直接渲染 `.pptx`**（`preview_svg.py` 已改为调用 LibreOffice），
  与 PPT 内容逐页一致；旧的手绘 SVG 近似版已废弃，避免与 `build_deck.py` 漂移。
- `raw/`、`assets/`、`_preview/` 是中间产物，可删。
