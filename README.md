# Agents — 智能体系统中的恶意 Skill 威胁（受控研究）

> 研究方向：**大模型攻击与安全**。本仓库复现「恶意第三方 skill 如何威胁智能体的使用者」，
> 包含一个受害者基线智能体、四类攻击 PoC，以及组会汇报幻灯。
>
> ⚠️ **RESEARCH-ONLY / 免责声明**：所有攻击均在**本地沙箱 + 合成假数据**下进行，
> 外传只发往**本机** mock 接收端，危险操作只作用于隔离沙箱内的假文件。
> 仅用于**防御性安全研究与教学**，请勿用于任何未授权的真实系统。

## 这是什么

基于自研 Agent 框架 **hello-agents** 搭建一个「私人助理」受害者智能体（持有合成隐私 + 假密钥 +
工具调用观测探针），演示一个**看似人畜无害**的第三方 skill 如何发起四类攻击。在 `deepseek-chat`
驱动下，四类攻击 **4/4 全部复现成功**。

| 攻击 | 伪装成 | 用户以为 | 实际危害 | 利用的框架弱点 |
|---|---|---|---|---|
| **T1** 间接提示注入 | 网页摘要 | 总结网页 | 泄漏隐私日程 / 银行卡尾号 | 信任工具**返回**（结果原样进上下文）|
| **T2** 数据/密钥外泄 | 云备份 | 备份备忘 | 偷传 6 个密钥到攻击者 | handler = 任意**代码** + 拿到全量 env |
| **T3** 工具投毒 | 合规校验 | 查日程 | 劫持工具选择 / 抢首调权 | 信任工具**描述**（拼进系统提示）|
| **T4** 越权/危险执行 | 缓存清理 | 清理缓存 | 读机密 PIN + 删文件 | “安全”TerminalTool 白名单可**绕过** |

## 目录结构

```
ch09/   上下文工程 demo：ContextBuilder(GSSC) / NoteTool / TerminalTool(+漏洞复现)
ch10/   MCP demo：自定义 MCP server + MCPTool 发现/调用
secskill-lab/
  baseline_agent.py   受害者基线 agent（ProfileTool + 观测探针 + 合成假数据）
  skill_loader.py     SKILL.md 风格 skill 加载器
  collector.py        本地 mock 外传接收端（仅 127.0.0.1）
  poc_t1_injection.py / poc_t2_exfiltration.py / poc_t3_tool_poisoning.py / poc_t4_dangerous_exec.py
  skills/benign/...               良性 skill 示例（memo）
  skills/research_malicious/...   四类恶意 PoC skill（均带 RESEARCH-ONLY 标注）
slides/  组会幻灯：main.tex（Beamer 源）+ main.pdf（编译产物）
```

## 复现步骤

```bash
# 1) Python 3.12 隔离环境（系统 Python 过新时尤其需要）
uv venv --python 3.12 .venv         # 或: python3.12 -m venv .venv
# 2) 安装框架（含 fastmcp/torch 等）
.venv/bin/pip install "hello-agents[all]==0.2.8"
# 3) 配置模型：复制并填写 .env（不要提交！）
cp .env.example .env                # 然后填入 LLM_API_KEY 等
# 4) 不需要 API 的本地 demo
.venv/bin/python ch09/02_note_terminal_demo.py
# 5) 四类攻击 PoC（需要 LLM API）
.venv/bin/python secskill-lab/poc_t1_injection.py
.venv/bin/python secskill-lab/poc_t2_exfiltration.py
.venv/bin/python secskill-lab/poc_t3_tool_poisoning.py
.venv/bin/python secskill-lab/poc_t4_dangerous_exec.py
```

## 幻灯

`slides/main.pdf` 可直接用于汇报；重新编译：

```bash
cd slides && latexmk -xelatex main.tex     # 需 texlive + ctex(fandol)
```

## 致谢

实验基于 Datawhale 开源教程《Hello-Agents：从零开始构建智能体》提供的 `hello-agents` 框架。
