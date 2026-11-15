---
layout: post
title: "Agent Infra Daily｜2026-11-15：从可恢复任务走向可验证执行契约"
date: 2026-11-15 08:00:00 +0800
summary: "周日独立抽查未确认过去24小时新的P0正式发布；回顾运行时恢复、工具治理与Sandbox故障域，强调执行账本与证据质量。"
tags: [agent-infrastructure, cloud-agent, durable-execution, sandbox, weekly-review]
---

## 今日核心判断

**可恢复的 Agent 并不自动等于业务上正确、安全且只执行一次的 Agent。** 过去约24小时独立抽查的官方版本、项目说明与研究队列，尚未核实足以定性为新P0生产架构/标准发布的事件。以下为近期证据的对比复盘，**不是把旧公告称作今日新品**。

## 重大进展与证据边界

1. **LangGraph 严格恢复与流取消（历史对比）。** Python 1.2.20 为每次 interrupt 分配独立 ID，严格恢复拒绝过期答案；JS 1.7.3 修复消费者退出流后剩余节点继续运行的问题。它们分别约束恢复答案与任务生命周期，不能证明远端工具调用具备 exactly-once。来源：https://github.com/langchain-ai/langgraph/releases 、https://github.com/langchain-ai/langgraphjs/releases
2. **OpenShell 共享监督与审计（历史对比）。** 官方 v0.1.7 说明实验性共享 Supervisor、故障接管与 OCSF 1.8.0 审计。共享进程降低控制面开销的潜力，需要与故障域扩大、连接重建、审计兼容成本共同评估；无独立百万用户基准。来源：https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.7
3. **AWS Agent Registry（已编辑核验的旧证据）。** 2026-10-21（北京时间）的一手架构文章展示 Discover/Instantiate/Execute 分离，Registry 发现已批准的 MCP/A2A 描述，不直接提供调用凭证。它是参考实现，不是跨厂商统一标准或生产吞吐量证明。来源：https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry

## 厂商路线、标准与研究

LangGraph 偏向应用工作流 Checkpoint 与中断语义；OpenShell 偏向计算隔离、监督、审计；AWS Registry 偏向工具发现与治理入口。**Tradeoff**：通用运行时接口可降低迁移成本，却不能抹平各后端对隔离、状态持久化、授权传播的差异。OCSF 1.8.0 可用于审计事件结构化，但不等于工具授权标准；MCP/A2A 的协议互联也不等于会话级策略已落地。今天未确认可提升这些结论成熟度的新独立技术论文或正式标准。

## 7天与30天趋势雷达

- **加强（工程信号，非已验证行业采用率）**：恢复时审批版本校验、取消传播、执行生命周期治理；近期多项目出现相关实现。
- **加强但低置信**：Registry/Gateway 工具治理。仓库仅有一项已编辑核验的 AWS 一手事件支持，尚不足以推断行业普及。
- **待证实**：独立 Durable Runtime 控制面、可替换 Sandbox Backend、长期记忆与 Context 分层、Agent 自我改进；现有正式趋势账本未积累充分已核验证据。
- **尚无推翻证据**：上述假设没有完成独立反例审阅，不能因没有新事件就判定失败。

## 百万用户 Cloud Agent：本周建议

优先落地 **TaskCheckpoint → AuthorizationFence → ExecutionLedger → ToolDispatcher → Reconciler** 五段契约。每个副作用操作记录 tenant_id、task_id、attempt_id、policy_version、idempotency_key、外部回执和对账状态；恢复、取消和重试必须重新检查权限，远端结果不明时先对账再重试。建立四类故障注入：断线、撤权、Sandbox 重建、外部成功但回执丢失；统计重复副作用、越权执行、p99恢复/停止时延和单位成功任务成本。以上均为**待验证工程方案**，不声称已有Benchmark。

## 周日独立信源审阅与数据缺口

独立抽查 LangGraph、LangGraph.js、OpenShell 的官方发布页面，并对照仓库已有研究队列；这是**有限抽查而非完整漏报审计**。北京时间11月15日08:00时，`intel/daily/2026-11-15.json` 尚未生成。最近11月14日快照：19/19信源抓取成功、96条候选、665条跨日未核验候选；独立Gold样本0，重要事件召回率不可计算。抓取成功不能代表覆盖完整，候选不等于已核验事件，Sitemap lastmod不作为事件日期。当前仅有2条已编辑核验的长期事件，5条趋势假设中1条有已核验证据。优先补做Gold漏报样本、队列去重与高优先级候选一手核验。

两条已登记的2027-03-31预测仍开放，不改概率或判定条件，不提前判YES/NO。长期KG没有充分新证据，今日只提交空增量。
