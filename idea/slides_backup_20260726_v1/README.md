# slides/ — 组会汇报材料（Do Not Mention 主讲 + SCR / HalluSquatting 补充 → 我的 idea）

**生成日期**：2026-07-26 · 图片优先、文字少、25 页、约 28 分钟。

## 直接用的文件
- **`组会_Do_Not_Mention_三篇.pptx`** — 可编辑 PPT（15 张图内嵌，含逐页演讲备注）。
- **`组会_Do_Not_Mention_三篇_预览.pdf`** — 可直接放映的高清预览（CJK 字体已固化，换机器不掉字）。
- **`演讲稿_SPEECH.md`** — 逐页口述稿 + 时间分配表（≤30 分钟）。

## 图片来源（`figures/`）
- **截自原论文（4 张）**：`dnm_fig1_shadow`（计算器 vs 反弹 shell）、`dnm_fig3_funnel`（98,380→157 漏斗）、
  `scr_fig1_chain`（三-skill 组合链）、`hallu_fig1_threat`（威胁模型 0–6 步）。
- **自绘（11 张）**：roadmap / skill 背景 / SCR 结果 / 幻觉率 / V1-V2 / E2E RCE / 验证质量 / RQ1-3 /
  **整合中心图** / 我的 acquisition funnel / 先导结果。数字均与 `../27`、`../28` 的“原文核对”一致。

## 重新生成（改字/改色/改数据后）
```bash
cd slides
.venv/bin/python make_figures.py      # 自绘图 SVG -> figures/*.png（改数据在此文件）
.venv/bin/python build_deck.py        # 生成 .pptx（改文案/顺序在此文件）
.venv/bin/python preview_svg.py       # 生成预览 .pdf（本机无 LibreOffice 时用它看效果）
```
- 环境：`uv venv --python 3.12 .venv` + `uv pip install python-pptx Pillow`；渲染用系统 `rsvg-convert` / `magick`。
- 截图重裁：`raw/` 是论文整页 200dpi 渲染，改裁剪参数见对应 `magick -crop` 命令历史。
- 字体：中文用 **Alibaba PuHuiTi 3.0**（本机已装），等宽用 JetBrains Maple Mono。

## 说明
- 本机无 LibreOffice，无法把 .pptx 直接渲染成图；预览 PDF 由 `preview_svg.py` 独立生成、与 PPT 内容一致，用于校对与放映。
- `raw/`、`assets/`、`_preview/` 是中间产物，可删。
