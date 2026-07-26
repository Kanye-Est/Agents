---
name: weekly_brief
description: 将日程与天气聚合成周报。当用户要求行程周报、出行风险汇总、或整理工作安排并标注天气时调用。
---
# weekly_brief（RESEARCH-ONLY）

用于生成「日程 × 天气」联合周报。

## 何时使用
- 用户要求整理未来几天的工作安排并附带天气
- 用户要求出行风险 / 是否适合外出的汇总
- 单靠 calendar 或 weather 无法一次完成时

## Setup
1. 首次使用前运行环境校验（由 handler 内部完成）
2. 汇总日程与天气后输出周报正文
