# 组会汇报 Slides — Agent 扩展授权中的制品身份漂移

Goose v1.45.0 Case Study 与多框架 Benchmark 计划。
**PRIVATE — Research Discussion / Coordinated Disclosure Pending**：仅限组会内部讨论，请勿外传或公开。

## 文件清单

| 文件 | 用途 |
|---|---|
| `index.html` | 幻灯片本体（单文件，全部 CSS/JS 内联，1920×1080 固定 16:9 舞台） |
| `slides.pdf` | PDF 导出版（逐页 1920×1080 静态快照） |
| `SPEAKER_NOTES.md` | 每页讲解要点与计时建议 |
| `SOURCES_AND_CLAIMS.md` | 每项 slide 主张对应的冻结证据文件（claim → evidence 表） |
| `preview/slide-*.png` | 逐页渲染截图（视觉审阅用） |
| `scripts/screenshot.mjs` | 逐页截图 + 溢出自动检测 |
| `scripts/export-pdf.mjs` | PDF 导出 |

## 本地演示

直接用浏览器打开 `index.html`（需要联网加载 Google Fonts；断网时回退系统字体）：

```bash
xdg-open index.html      # 或 firefox / chromium index.html
```

- **翻页**：← / →、空格、PageUp / PageDown、Home / End、滚轮、触屏滑动
- **进度条**：顶部橙色进度条；底部有 Prev / Next 按钮
- **行内编辑**：鼠标悬停左上角或按 `E` 进入编辑模式，点击任意文字直接修改，`Ctrl+S` 保存到 localStorage（仅本机浏览器）

## 截图与 PDF 导出

```bash
npm install            # 首次：安装 playwright（浏览器复用 ~/.cache/ms-playwright）
node scripts/screenshot.mjs   # 重新生成 preview/ 截图并做溢出检测
node scripts/export-pdf.mjs   # 重新生成 slides.pdf
```

PDF 为静态快照：动画以最终状态呈现，交互（翻页/编辑）不保留。

## 内容边界（重要）

- 结论上限 **Level 2（authorization-reference drift / deferred-resolution authorization）**；
- 全篇不使用：TOCTOU、arbitrary code execution、"绕过批准"、跨框架普遍性、N=3、内容完整性、因果证明；
- 哈希只显示前 8–12 位；不含 VM 公网 IP、API key 或可直接滥用的操作细节；
- 所有实验数字均出自 `~/goose-canary-archive/` 冻结材料，对应关系见 `SOURCES_AND_CLAIMS.md`。

## 关于 PPTX

本项目为 frontend-slides 原生 HTML 幻灯片，**不支持真正的 .pptx**。如需投屏用文件，请使用 `slides.pdf`；不要把 HTML/PDF 改后缀冒充 PPTX。
