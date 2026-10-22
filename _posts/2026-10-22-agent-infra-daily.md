---
layout: post
title: "Agent Infra Daily · 2026-10-22｜Always-on Agent 与跨模型云控制面"
date: 2026-10-22 08:37:00 +0800
summary: "Claude Duet研究预览、Google Cloud引入OpenAI模型私有预览、Oracle行业Agent Studio规划，以及数千科研Agent并行实验，揭示长期任务、模型供应与业务治理的分层趋势。"
tags: [agent-infra, strategic-analysis, cloud-agent, agent-runtime, model-routing, governance, multi-agent]
---

## 今日核心判断

**Agent Infrastructure 的竞争边界正从模型与聊天界面转向长期任务控制面、用户授权、业务上下文和执行环境。** 10月21日三份一手公告提供不同成熟度的信号：Anthropic 发布 Claude Duet **研究预览**；Google Cloud 将 OpenAI 模型纳入 Model Garden，当前为**私有预览**；Oracle 公布行业 Agent Studio，**计划未来12个月内提供**。三者不是同一天正式 GA 的成熟 Runtime，不能把产品公告当作生产可靠性证据。

研究窗口：北京时间 **2026-10-21 08:42—2026-10-22 08:37**。官网只有10月21日发布日期，没有可核实的精确时分与时区；因此不声称所有事件严格落入分钟级24小时窗口。

## 关键行业与生态进展

### 1. Always-on Agent 正在成为独立产品形态（P0）

[Anthropic 官方发布](https://claude.com/resources/articles/claude-duet) 介绍 Claude Duet：继承 Claude 账户的记忆、Skills 和连接器，在独立云虚拟机及浏览器中处理后台任务；定期检查连接应用、主动发送简报，敏感动作等待批准。官方说明账户检查一般每数小时进行，而非不间断运行，后台检查也消耗用户计划额度；凭据处理沿用 Managed Agents 的隔离思路。

**架构信号**：Always-on 不等于一直保持活跃模型循环。真正需要的是 Trigger/Watch、Durable Task、Cloud Workspace、Approval、Notification 和成本预算的独立生命周期。对百万用户规模，应优先事件驱动与自适应轮询，而不是百万个常驻推理进程。

**证据边界**：Duet 当前为美国 Pro/Max 用户 waitlist research preview。官方承认可能误判优先级、漏掉检查间隔内的事件；未公布普适 SLA、长任务恢复率或每成功任务成本。

### 2. 模型供应与云平台控制面开始解耦（P0）

[Google Cloud 10月21日公告](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-brings-openai-models-to-customers) 宣布 OpenAI GPT-6 Astra、GPT-6.1 Sol、GPT-6 Luna 进入 Model Garden，提供统一的企业身份、审计、账单与数据边界，并支持本地 Codex 工具通过该平台推理。目前只向选定企业客户滚动开放 **private preview**；Zero Data Retention 与 Confidential Compute 等被标为 coming soon。

**架构信号**：模型 API、企业计费与策略入口可跨模型厂商整合，但 **Model Portability ≠ Agent State Portability**。模型切换仍可能改变工具调用、结构化输出、上下文压缩和安全表现。云平台争夺的是模型路由与治理控制面，而不是自动获得任务 Checkpoint 的跨运行时可移植性。

**证据边界**：官方预览公告不证明所有客户已可使用，不证明跨模型 Agent 质量等价，也没有通用端到端 TCO 基准。

### 3. 行业业务系统争夺 Agent 执行权（P1，计划阶段）

[Oracle 10月21日公告](https://www.oracle.com/news/announcement/oracle-ai-agent-studio-for-industry-applications-helps-accelerate-business-outcomes-2026-10-21/) 描述行业流程内的 Agent Studio：可复用业务工具、MCP、跨应用编排、测试、角色策略和监控。公告脚注明确该平台**计划在未来12个月内先于美国提供**，不能写成已 GA。

**架构信号**：通用 Runtime 解决任务如何可靠执行，行业平台掌握具体数据、角色、审批与业务规则。开放 MCP 降低连接成本，却不能替代业务授权和跨平台状态迁移。

## 技术路线与竞争格局

| 路线 | 控制面优势 | 关键代价/边界 |
|---|---|---|
| 个人主动 Agent（Duet 研究预览） | 统一用户上下文、云电脑、审批与主动触发 | 通知误报、检查成本、缺少规模化恢复证据 |
| 企业多模型云入口（Google Cloud 私有预览） | 模型选择、统一审计、身份、结算 | API 统一不等于 Task/Workspace 可移植 |
| 行业业务 Agent Studio（Oracle 规划） | 领域数据、角色、业务审批与流程 | 行业应用锁定、尚待交付与生产验证 |
| 自建 Cloud Agent 控制面（本站分析） | 独立 Task/Run、状态与权限契约 | 自担分布式一致性、安全及成本治理 |

**收敛**：长任务身份、最小权限工具执行、云端计算和可观测性成为共同基础能力。**分歧**：记忆由谁持有、委托权限归谁管理、工作空间能否迁移、后台检查与执行如何计费。

## 研究与可验证性

[OpenAI / PerturbAI / Scripps Research 10月21日披露](https://openai.com/index/scaling-ai-research-for-complex-biological-data/)：数千个 GPT-Rosalind Agent 并行分析小鼠脑细胞扰动数据并关联科学文献，报告在特定实验中 **32分钟**形成候选生物机制的 reasoning atlas。该结果支持“高扇出分析 → 证据汇聚 → 人类专家评估与后续实验”模式，但32分钟不是跨领域通用 Benchmark；生物机制尚需独立实验验证。

**历史基线，不是今日新事件**：[10月14日 Third Moment Research 案例](https://openai.com/index/third-moment-research/) 报告1万个并发 Agent、36–48小时研究会话。两项案例负载和指标不同，不能据此比较吞吐、成本或准确率。本窗口未核验到新的 MCP/A2A 正式互操作规范或可复现跨厂商状态迁移评测。

## 7日/30日趋势雷达

| 方向 | 判断 | 新证据/未知 |
|---|---|---|
| Proactive Always-on Agent | **加强** | Duet 新预览；缺真实恢复 SLA 和每任务成本 |
| 跨模型云平台控制面 | **加强** | Google Cloud 新私有预览；缺模型间行为等价证据 |
| 行业流程 Agent 治理 | **加强但待落地** | Oracle 规划；非 GA |
| 高扇出科研 Agent | **加强** | 新生物数据分析案例；需要复现和实验验证 |
| 跨厂商 Task/Workspace/Authority 可移植 | **待证实** | 模型可选择，不等于执行状态可迁移 |
| Agent RSI 长期自改进 | **待证实** | 自动化研究案例不足以证明稳定自我提升 |

## 大型 Cloud Agent 工程启示

**P0：长期任务控制面**。独立管理 Trigger、Task Journal、Run/Attempt、Workspace、Approval、Notification 与 ModelRequest。按用户限制后台检查频率、Token、工具调用和云电脑活跃时长；对凭据撤销、Worker 迁移、未知工具结果、重复投递和审批超时做故障注入。

**P0：授权与执行身份分离**。用户委托、Agent 身份、Task 代际、审批证据与 Sandbox 权限分别可审计。执行环境不因继承会话上下文而自动继承完整账号权限。

**P1：模型路由先于模型锁定**。跨模型比较任务成功率、工具误调用、人工接管率、P95 完成时间与每成功任务总成本；统一 API 不能替代正确性门禁。

**P1：平台与行业适配分层**。通用 Runtime 管理任务与恢复，Registry/Gateway 管理工具发现和权限，行业 Adapter 管理业务规则与审批。先验证跨应用失败补偿，再决定托管或自建。

## Sources

- 2026-10-21 [Anthropic — Introducing Claude Duet](https://claude.com/resources/articles/claude-duet)
- 2026-10-21 [Google Cloud — OpenAI models in Model Garden](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-brings-openai-models-to-customers)
- 2026-10-21 [Oracle — AI Agent Studio for Industry Applications](https://www.oracle.com/news/announcement/oracle-ai-agent-studio-for-industry-applications-helps-accelerate-business-outcomes-2026-10-21/)
- 2026-10-21 [OpenAI — Thousands of AI agents for biological data](https://openai.com/index/scaling-ai-research-for-complex-biological-data/)
- 2026-10-14 [OpenAI — Third Moment Research](https://openai.com/index/third-moment-research/)（历史基线）
