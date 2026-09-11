会议纪要：工具注入攻击绕过现有防御机制
会议时间：2026-09-09 21:06 – 21:57 参会人员：世宇、齐越、韩老师、罗老师 记录说明：本纪要依据录音 AI 转写整理，经人工核对修订；授权相关条款依会议决定与 idea/52 Amendment 1 整理。

一、会议议程
安全漏洞攻击方式分析
现有防御方法的局限性
攻击场景设计与实验规划
代码混淆技术应用探讨
二、核心内容
1. 攻击方式分析
攻击以代码形式表现，直接执行恶意功能（如窃取指定 workspace 文件、利用当前工具授权执行操作）；
攻击不出现在 context window，因此基于 context 的防御方法无法防御；
文本侧防御（如 ACE，NDSS 2026）、reputation/signature 方法、install-time scanner 方法均无法有效防御此类攻击。
2. 现有防御方法的局限性
Install-time scanner（静态扫描类）：只在安装时扫描一次；仅读代码结构、不运行代码；无法检测经过混淆的代码；
Runtime 轨迹审计类：只有当恶意操作反映在 work trajectory 中才能被检测——若恶意代码不将结果放入工具返回值，此类方法也无法检测；
SkillDetonate 类沙盒引爆：在沙盒中于 OS 层监控 syscall（Linux 上经 eBPF 实现）可以检测此类攻击，但：(a) 代价昂贵、得不偿失；(b) 沙盒类防御本身存在被规避的可能（如检测虚拟环境、延迟执行等）。此两点作为论文中对该类防御的回应口径，引用文献论证，不进行真实沙盒规避实验。
3. 攻击场景设计与实验规划
需设计攻击代码并明确攻击目标；参考 Oakland 2026（IEEE S&P'26，Parasites in the Toolchain, arXiv 2509.06572）设置四种攻击目标：
窃取隐私凭证文件
篡改 workspace 文件
将文件外传至指定位置
远程命令执行 / 任意文件写（本期不实施，设计预留）
恶意代码（安全替身载荷，效应受实验信封约束、经生成后验证器门控）建议由 coding agent 生成；韩老师举例可考虑使用防御较弱的模型，具体型号后续确定；
E2×P-ctx 路线（经 context 注入指令）不采用：凡进入 LLM context 即可被 runtime 轨迹方法检测；本项目攻击确定为 E2×P-direct——完全由工具主导执行、完全绕过 LLM 防御机制。
4. 代码混淆技术应用
代码混淆是绕过静态扫描防御的关键技术，常用方法包括 control flow flattening 等；
混淆在工具知识产权保护中亦有合法用途（论文中可作 dual-use 平衡论述）；
具体方法参考 USENIX Security 2024（Fang et al., "Large Language Models for Code Analysis: Do LLMs Really Do Their Job?"，§2.4 五种混淆方法：DE / DCI / CFF / SS / WSM）。
5. 实验实施计划
先实现最小化攻击实验验证可行性；
测试开源与闭源 agent 框架（含 Claude Code）对攻击的防御能力，含对静态扫描器的检出率实测（对应实验计划第二步）；
关注 agent framework 中第三方工具的使用情况；
agent 侧测试模型采用韩老师指定的 agentic 后训练模型：千问 3.8 27B、DeepSeek V4 flash。
6. 论文写作思路
参考 Oakland 2026 文章结构组织论文：攻击先行 → 测量随后的 pipeline；漏洞挖掘 pipeline + 攻击场景设计；
强调攻击完全由工具链执行、绕过 LLM；突出漏洞的广泛性与危害严重性；对比现有防御方法的高成本与低可行性。
三、决议与授权条款
采用工具主导的攻击方式（E2×P-direct），完全绕过 LLM 防御机制；E2×P-ctx 路线废止；
对 SkillDetonate 类防御以上述两点（成本 + 沙盒可规避性）作为论文回应口径；
先行开展最小攻击实验验证可行性；实验范围、判据、安全信封以 idea/52 §14 Amendment 1（UTCS 最小攻击实验协议）为准，包括：
对象：Goose 锚点；危害目标 G1（凭据窃取替身）/ G2（外传替身）/ G3（可逆 workspace 篡改替身）；
载荷由 coding agent 按冻结安全替身规格生成，经双重验证器门控后施加五种混淆；
每格 3 次、五判据（含 trajectory_absent 轨迹缺席与 benign_function_preserved 功能回归）；
第二步（同一授权内）：对静态扫描器实测检出率；
安全信封：仅合成凭据（sk-FAKE）、网络仅限 127.0.0.1 回环、marker 效应、可逆操作、无真实破坏；
本期不含：G4（RCE 替身）与跨对象扩展（OpenCode / Gemini CLI）保持 deferred，实施前需另行确认；
授权生效：以本纪要归档件（含 SHA256）为准；生效记录（EFFECTIVE RECORD）追加至 idea/52 时须显式引用 Amendment 1 落盘后的 sha256。
四、行动事项
执行人    任务
世宇 / 齐越    实现最小化攻击实验，验证攻击可行性
世宇    阅读 Oakland 2026（Parasites in the Toolchain）文章，制定漏洞挖掘 pipeline
世宇    研究代码混淆技术（USENIX Sec'24 五法），准备相关资源
全体    测试开源与闭源 agent 框架对攻击的防御能力
五、会议总结
本次会议确认了以工具链直接执行、完全绕过 LLM 防御的攻击技术路线，梳理了现有三类防御（静态扫描 / 轨迹审计 / 沙盒引爆）的局限，明确了最小攻击实验的范围与授权。下一步重点为实现最小化攻击实验、验证可行性，并参考 Oakland 2026 结构组织论文。