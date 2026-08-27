# 文献速查表

> 只保留写 related work / 开题会用到的信息。  
> 更新：2026-07-16

**本 idea 四段：** 缺口 → 检索 → 安装 → 调用+载荷

---

## 1. 必读（P0）

| 论文 | 一句话 | 关键数字 | 对应我们 | 链接 |
|------|--------|----------|----------|------|
| **IPI** | 毒文档先要被检索到，否则注入白搭 | Vanilla≈0%，CEM≈100% | 叙事模板 | [2601.07072](https://arxiv.org/abs/2601.07072) |
| **Skill-Inject** | skill **已加载后**执行恶意指令 | 最高约 80% ASR | post-load 对照，别横比 | [2602.20156](https://arxiv.org/abs/2602.20156) |
| **Poise** | 单行 setup + 旁路脚本，任务仍成功 | ~89% ASR | 装后怎么打 | [2606.07943](https://arxiv.org/abs/2606.07943) |
| **ToolHijacker** | 工具库：**检索 + 选择** 两段可优化 | ASR 常 80%+ | 库内 selection | [2504.19793](https://arxiv.org/abs/2504.19793) |
| **ToolTweak** | 改 name/desc 抢**同类**工具 | 20%→81% | 说明跨域≠同类 | [2510.02554](https://arxiv.org/abs/2510.02554) |
| **2605.11418** | registry 上 Discovery / Selection / 扫描 | 检索胜率 86%，选中 77.6% | **最强 pre-load 验收** | [2605.11418](https://arxiv.org/abs/2605.11418) |
| **Skills 综述** | progressive disclosure；acquisition 术语 | 三层加载 | 术语与架构 | [2602.12430](https://arxiv.org/abs/2602.12430) |
| **MSB** | MCP 攻击 12 类 taxonomy | FE / 偏好 / 撞名… | Stage2 菜单 | [2510.15994](https://arxiv.org/abs/2510.15994) |
| **MPMA** | MCP 偏好操纵（广告+遗传） | DPMA 常 100% ASR | 装后描述怎么写 | [2505.11154](https://arxiv.org/abs/2505.11154) |
| **Do Not Mention** | 真实市场恶意 skill 规模 | 9.8 万 skill → 157 恶意 | 生态真实会装 | [2602.06547](https://arxiv.org/abs/2602.06547) |
| **You Told Me** | README/安装文档诱导外泄 | ~85% | 权威通道促装 | [2603.11862](https://arxiv.org/abs/2603.11862) |
| **SCR** | 单 skill 无害，组合有害；信任促装 | TrustLift 促装 >83% | 二重依赖 | [2606.15242](https://arxiv.org/abs/2606.15242) |
| **HalluSquatting** | 显式 install 请求被幻觉名/slug 抢注劫持 | fetch / invocation / RCE 40%–100% | **真实 install E2E 强邻居；S0 不同** | [2607.07433](https://arxiv.org/abs/2607.07433) |
| **SearchGEO** | 多源伪证据诱导 agent 背书 skill 并输出安装命令 | 跨生态：Claude 0/18；GPT-5.4-mini 17/18 | **install command ASR；未执行安装** | [2606.16821](https://arxiv.org/abs/2606.16821) |
| **Skills That Don't Exist** | agent 推荐不存在的 skill，攻击者可抢注名称 | agent 平均 36.9%；n=1 显式授权安装 PoC | recommendation→delivery；非自主安装基准 | [2607.12340](https://arxiv.org/abs/2607.12340) |

---

## 2. 重要（P1）

| 论文 | 一句话 | 关键数字 | 对应我们 | 链接 |
|------|--------|----------|----------|------|
| **MCPTox** | 真实 MCP 工具描述投毒 | 部分模型 >70% | T3 / 描述投毒 | [2508.14925](https://arxiv.org/abs/2508.14925) |
| **SkillJect** | 自动生成毒 skill | 跨平台优于手工 | 装后内容优化 | [2602.14211](https://arxiv.org/abs/2602.14211) |
| **SkillAttack** | **不改 skill**，只改用户 prompt 挖洞 | 对抗 0.73–0.93 | 正交，别混 | [2604.04989](https://arxiv.org/abs/2604.04989) |
| **KidnapRAG** | 多步毒文档劫持推理链 | Bait→Link→恶意 | 多步诱导类比 | [2607.00422](https://arxiv.org/abs/2607.00422) |
| **How Many Tools** | 先 shortlist 再给模型 | top-k 设计 | 市场检索合理 | [2605.24660](https://arxiv.org/abs/2605.24660) |
| **AgentSkillOS** | 大规模 skill 检索+编排 | 200～20 万 skill | 规模动机 | [2603.02176](https://arxiv.org/abs/2603.02176) |
| **Skills Not Islands** | skill 有依赖图 | — | companion 依赖 | [2607.01136](https://arxiv.org/abs/2607.01136) |
| **Dynamic Mal. Skills** | 运行时再往 skill 里注毒 | 非平凡成功率 | 装后变毒 | [2606.16287](https://arxiv.org/abs/2606.16287) |
| **SkillTrojan** | skill 后门 | 至 97% ASR | 装后危害上限 | [2604.06811](https://arxiv.org/abs/2604.06811) |
| **BadSkill** | skill 里塞后门模型 | 97–99% ASR | 同上，勿撞贡献 | [2604.09378](https://arxiv.org/abs/2604.09378) |
| **AgentDojo** | 工具返回劫持后续动作 | — | 假错误通道 | [2406.13352](https://arxiv.org/abs/2406.13352) |
| **SkillSieve** | 扫描恶意 skill | F1 0.92 | 防御对照 | [2604.06550](https://arxiv.org/abs/2604.06550) |
| **Neutral Prompting Attacks** | skill 诱导模型幻觉包并输出 `pip install` | 最高约 63%（依模型/数据集） | 包生态邻接；命令输出≠执行 | [2605.29354](https://arxiv.org/abs/2605.29354) |

---

## 3. 扩展（P2，按需）

| 论文 | 一句话 | 链接 |
|------|--------|------|
| MCPSecBench | 多平台 MCP 攻击面 | [2508.13220](https://arxiv.org/abs/2508.13220) |
| PhantomSkill | 恶意藏辅助资源 | [2606.19191](https://arxiv.org/abs/2606.19191) |
| ShareLock | 多 tool 分片重组，ASR>90% | [2606.27027](https://arxiv.org/abs/2606.27027) |
| AIRGuard | 运行时权威门降 ASR | [2605.28914](https://arxiv.org/abs/2605.28914) |
| MOSAIC | 无害 CLI 组合致害 96% | [2607.02857](https://arxiv.org/abs/2607.02857) |
| Over-Privilege | 爱选过高权限工具 | [2606.20023](https://arxiv.org/abs/2606.20023) |
| LASM 综述 | agent 攻击面分层 | [2604.23338](https://arxiv.org/abs/2604.23338) |
| InjecAgent | 工具 IPI 早期基准 | [2403.02691](https://arxiv.org/abs/2403.02691) |
| Early Skill PI | Skill-Inject 前身短文 | [2510.26328](https://arxiv.org/abs/2510.26328) |
| Repo-Aware Skills | 高安装量+仓库风险 | [2603.16572](https://arxiv.org/abs/2603.16572) |

---

## 4. 和我们四段怎么对上

| 阶段 | 主要引用 |
|------|----------|
| **缺口** | MSB 假错误 · AgentDojo · KidnapRAG |
| **检索** | IPI · ToolHijacker · 2605.11418 · How Many Tools |
| **安装**（部分覆盖） | HalluSquatting（显式请求、真实 E2E）· SearchGEO（命令输出）· Skills That Don't Exist（推荐后显式安装 PoC）· You Told Me · SCR |
| **调用+载荷** | Skill-Inject · Poise · ToolTweak · MPMA · SkillTrojan |

---

## 5. 别和谁比数字

| 他们 | 我们 |
|------|------|
| Skill-Inject 80%：**已加载**后执行 | 预装跨域选中 5% / 搜到不装 |
| ToolTweak 81%：**同类**天气工具 | **跨域** weather vs 全能助手 |
| ToolHijacker 80%+：工具**已在库** | 还要过自主 acquisition 与实际 install |
| SkillAttack：不改 skill，改用户话 | 我们改 skill 供应链 |
| HalluSquatting：用户明确说 **install X** | 用户只给普通任务，agent 因能力缺口自行 acquisition |
| SearchGEO：输出精确安装命令 | 区分 emitted / parsed / executed / installed，并继续测 invoke / payload / task_ok |

---

## 6. 本地 PDF

```
idea/papers_phase8/   11 篇
idea/papers_phase9/   7 篇
idea/papers_phase10/  4 篇
ANL/2601.07072v1.pdf  IPI
其余：https://arxiv.org/pdf/<编号>
```

---

## 一句话结论

文献已覆盖 **显式 install 请求下的真实 E2E** 和 **安装命令输出 ASR**。仍缺的是：用户只给普通任务时，agent 是否因能力缺口自行检索并**实际执行安装**，以及从 `gap_triggered` 到 `task_ok` 的逐段条件概率——这才是本 idea 应守住的主菜。
