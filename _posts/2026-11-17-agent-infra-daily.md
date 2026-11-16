---
layout: post
title: "Agent Infra Daily｜2026-11-17：恢复正确性与执行治理的分层"
date: 2026-11-17 08:00:00 +0800
summary: "过去24小时未核实重大P0正式发布；比较LangGraph严格恢复、Codex多会话和OpenShell沙盒治理的边界，提出可测试的百万用户Cloud Agent执行契约。"
tags: [agent-infrastructure, cloud-agent, durable-execution, sandbox, security]
---

## 今日核心判断

**Agent 运行时的竞争焦点不是能否重新打开会话，而是能否在重试、撤权、取消和沙盒重建后保持业务正确性。** 本期有限范围的官方一手资料检索未确认北京时间11月16日08:00至11月17日08:00期间新的P0级正式架构、标准或生产级重大能力发布。不能把计划中的里程碑、预发布或RSS候选当成已交付事实。

## 重要进展与证据边界

1. **LangGraph：恢复语义更加严格（历史对照，非今日发布）。** 官方11月5日发布的langgraph 1.2.20为每次任务内interrupt分配独立ID，并增加拒绝过期中断答案的strict resume；11月6日SDK 0.4.14暴露对应参数。这约束人工审批的状态版本，却不能证明外部API只执行一次。[官方发布](https://github.com/langchain-ai/langgraph/releases)
2. **LangGraph.js：取消传播得到修复（历史对照）。** 11月10日北京时间对应的1.7.3版本在流消费者退出迭代时停止后续运行；已发送的外部写入仍可能成功，必须单独对账。[官方发布](https://github.com/langchain-ai/langgraphjs/releases)
3. **OpenShell：Sandbox安全与资源治理持续演进（历史对照）。** 官方版本说明包含网络代理、Supervisor、审计和资源使用的改进，但不能据此推出百万用户隔离与故障恢复的SLA。[官方发布](https://github.com/NVIDIA/OpenShell/releases)

## 架构路线与Tradeoff

- **工作台/会话层（Codex等）**：优化多会话导航和后端切换，优势是体验；代价是会话历史不等于可迁移执行状态。[Codex Releases](https://github.com/openai/codex/releases)
- **编排/Checkpoint层（LangGraph等）**：状态持久化和人工中断恢复，优势是可观测可重放；代价是外部副作用需要应用层补偿、幂等与对账。
- **隔离执行层（OpenShell等）**：隔离、网络治理、审计，优势是缩小工具风险；代价是Sandbox生命周期、成本和跨租户故障域复杂度。
- **工具治理层（AWS Agent Registry参考架构）**：发现与调用凭证分离有助于统一管理；厂商参考实现并非跨厂商互操作的生产证明。[官方技术文章](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry)

## 标准与研究

MCP/A2A可解决部分工具或Agent交互接口问题，但**协议兼容不自动提供跨步骤授权、Exactly-once外部写入、持久Workspace或租户隔离**。本期没有核实新的正式标准版本；不将候选变更视为标准落地。[MCP官方规范](https://modelcontextprotocol.io/specification/) · [A2A官方仓库](https://github.com/a2aproject/A2A)

## 7天 / 30天趋势雷达

| 方向 | 7天判断 | 30天判断 | 证据边界 |
| --- | --- | --- | --- |
| 恢复与取消语义 | 加强 | 加强 | 多个正式版本改进，但缺少跨后端生产数据 |
| Sandbox最小权限和审计 | 加强 | 加强 | 官方版本与文档，缺少独立故障注入 |
| 统一跨厂商授权标准 | 待证实 | 待证实 | 参考架构不等于普遍采用 |
| Exactly-once业务副作用 | 待证实 | 待证实 | 尚无通用保证，不可将Checkpoint等同于事务 |
| 百万Agent规模经济性 | 待证实 | 待证实 | 无可比独立成本基准 |

## 百万用户Cloud Agent：具体工程建议

**先实施执行正确性闭环，而非先增加复杂多Agent编排。**

1. 定义 `SessionRecord`、`WorkspaceVersion`、`TaskCheckpoint`、`AuthorizationFence`、`ExecutionLedger` 五个独立对象；所有可写工具调用绑定tenant、principal、task、attempt、authorization_version和idempotency_key。
2. 在派发前写入持久账本；收到超时或断线时先查询外部回执或业务状态，不对不确定的写操作盲目重试。无法提供幂等键的外部系统使用人工确认或补偿流程，不声称全链路Exactly-once。
3. 故障注入矩阵覆盖：审批后撤权、流取消后工具仍运行、Sandbox销毁重建、Provider切换、外部写入成功但回执丢失。跟踪重复副作用率、越权执行数、恢复p99、闲置Sandbox成本和每成功任务总成本。

## 情报质量与预测边界

最近可用的2026-11-16采集质量快照：19/19信源抓取成功、62条当期候选、668条跨日未核验积压；独立Gold样本为0，重要事件召回率**无法计算**。2026-11-17的日快照在本次研究时尚不存在。抓取成功率不是事件覆盖率，候选均未自动核验。长期趋势库仅有少量独立审核事件，不能将本日报推论自动提升为KG事实。两项2027-03-31到期预测保持原始条件和概率，不提前裁决。

## 官方Sources

- https://github.com/langchain-ai/langgraph/releases
- https://github.com/langchain-ai/langgraphjs/releases
- https://github.com/openai/codex/releases
- https://github.com/NVIDIA/OpenShell/releases
- https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry
- https://modelcontextprotocol.io/specification/
- https://github.com/a2aproject/A2A

> 本日报是基于截至北京时间2026-11-17早间可核验的一手公开资料形成的有限研究判断，不包含未经证实的厂商性能或采用率数字。
