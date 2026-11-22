---
layout: post
title: "Agent Infra Daily｜2026-11-22：恢复正确性与信源漏报审计"
date: 2026-11-22 08:00:00 +0800
summary: "过去24小时未独立确认新的P0正式发布；周日复核Agent恢复、权限和执行对账，并审视情报队列质量。"
tags: [agent-infrastructure, cloud-agent, durable-execution, sandbox, research-quality]
---

# Agent Infra Daily｜2026-11-22

> **核心判断：** Agent 远程会话与状态持久化能力持续演进，但“恢复连接”“恢复任务状态”“恢复授权”和“避免外部副作用重复”仍是四个不同契约。过去约24小时的有限官方资料独立检索未确认足以升级为P0的新正式架构或标准发布；不以RSS候选或Sitemap lastmod冒充发布事实。

## 重大进展及证据边界

1. **远程会话与可恢复执行（历史基线，非今日新品）。** Codex 0.171.0 的远程非交互执行与 LangGraph 的严格恢复机制表明开发者体验和状态正确性都在完善。远程连接本身不保证跨Worker恢复、撤权传播或Exactly-once外部调用。官方资料：[Codex releases](https://github.com/openai/codex/releases)、[LangGraph releases](https://github.com/langchain-ai/langgraph/releases)。
2. **Agent Server 与自动化职责分离（官方架构基线）。** OpenHands SDK 官方README明确：SDK/Agent Server承担会话、工作区、工具和REST/WebSocket执行；OpenHands/automation负责调度、webhook、运行历史和派发。这种控制面/执行面拆分有利于故障隔离，但仍需要应用层任务账本和权限栅栏。来源：[OpenHands SDK](https://github.com/OpenHands/software-agent-sdk)。
3. **工具治理与权限链（历史已核验证据）。** AWS Agent Registry 的参考设计将受批准工具发现与调用凭据分开，支持工具治理层的设计方向；单一厂商教程不能证明跨平台标准成熟或百万用户可靠性。来源：[AWS官方参考架构](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry/)。

## 主流路线与 Tradeoff

- **Codex / Harness：** 远程执行和多会话交互体验强；跨进程状态迁移、MCP子进程沙盒和授权撤销仍需系统边界验证。
- **LangGraph：** 显式Checkpoint、Interrupt与状态归约适合复杂长任务；重放语义与外部API幂等不能混同。
- **OpenHands：** Agent Server与调度层分工清晰；会话状态、容器工作区和工具副作用需分别恢复。
- **托管云平台：** Registry、Memory、Policy与Sandbox减少自建成本，但可能引入云厂商身份模型、地域限制和升级语义锁定。

## 标准与研究

MCP工具协议和工具注册表解决互操作/发现的一部分问题，不自动提供跨步骤的主体绑定、撤权一致性或外部操作Exactly-once。未发现足够可靠的过去24小时官方标准变更证据，故不升级结论，也不捏造性能基准。

## 7天 / 30天趋势雷达

| 方向 | 7天观察 | 30天判断 | 反证或缺口 |
|---|---|---|---|
| 远程会话与恢复 | 加强（历史正式版本支持） | 加强但证据有限 | 缺跨Worker故障注入数据 |
| 工具注册与授权治理 | 待证实 | 低置信加强 | 单厂商参考实现不能代表采用率 |
| 可替换Sandbox与工作区 | 待证实 | 待证实 | 缺跨后端迁移与隔离基准 |
| 长期记忆与任务状态分层 | 待证实 | 待证实 | 缺独立质量/成本对照 |
| Agent自我改进闭环 | 待证实 | 待证实 | 缺可复验长期收益 |

“加强”是研究判断而非仓库趋势状态自动更新；未验证的新信息不进入长期KG。

## 百万用户 Cloud Agent：本周工程优先级

1. **Resume Gate：** 会话重新连接时验证Checkpoint schema、Workspace manifest/hash、身份和授权版本；禁止旧授权静默延续。
2. **Execution Ledger：** 每次副作用工具调用持久记录operation_id、幂等键、派发状态和外部回执；未知结果先对账，避免盲重试。
3. **故障矩阵：** 在滚动升级、取消/撤权竞态、Sandbox重建、流断线和响应丢失下分别测重复副作用率、越权率、恢复P95与单位成功任务成本。以上是建议测试项，不是已有Benchmark。

## 周日独立信源漏报审阅（有限范围）

截至最新可用的**2026-11-21**仓库快照，19/19信源抓取成功，81条当期候选、871条跨日未核验积压；Gold样本为0，无法计算重要事件召回率。今日2026-11-22采集快照尚不存在。独立抽查了OpenHands与LangGraph官方仓库/Release页面，但**未完成覆盖全部来源的漏报审计**；网页搜索结果存在索引滞后，不将其缺失当作无发布证明。优先建立人工核验Gold样本、去重与候选SLA，避免积压继续增长。

## 预测与知识图谱

两条截至2027-03-31的预注册预测均未到期，原条件、概率及未决状态保持不变。今日无足够的一手新证据触发长期Entity/Pattern/Trend实质更新，KG Delta为四组空数组。

## 官方 Sources

- [OpenAI Codex Releases](https://github.com/openai/codex/releases)
- [LangGraph Releases](https://github.com/langchain-ai/langgraph/releases)
- [OpenHands Software Agent SDK](https://github.com/OpenHands/software-agent-sdk)
- [AWS Agent Registry reference architecture](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry/)
