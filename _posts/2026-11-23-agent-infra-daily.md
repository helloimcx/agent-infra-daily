---
layout: post
title: "Agent Infra Daily｜2026-11-23：恢复语义与执行治理的证据边界"
date: 2026-11-23 08:00:00 +0800
summary: "过去约24小时有限官方检索未确认新的P0正式架构发布；区分预发布、持久恢复与副作用对账，聚焦百万用户Cloud Agent执行契约。"
tags: [agent-infrastructure, cloud-agent, durable-execution, tool-governance, research-quality]
---

# Agent Infra Daily｜2026-11-23

> **今日核心判断：** Agent 基础设施的竞争焦点仍是可恢复执行的正确性、授权边界与单位成功任务成本，而非单纯把会话重新连接。过去约24小时有限的一手检索没有确认足以认定为P0的正式新架构或标准发布；下列案例是有明确日期的历史对照，不是今日新品。

## 重大进展及证据边界

1. **Codex 预发布不等于正式交付。** GitHub 官方 Release API 可确认 Codex `rust-v0.173.0-alpha.4` 于 2026-11-21 00:35 UTC（北京时间11月21日08:35）发布，标注 `prerelease=true`。该事实只能说明存在测试版本，不能推断远程持久任务恢复、跨Worker兼容或生产SLA已经正式提供。来源：[官方 Release](https://github.com/openai/codex/releases/tag/rust-v0.173.0-alpha.4)。

2. **LangGraph 增量状态重放的边界（历史对照）。** 正式版 `langgraph==1.2.24` 于 2026-11-20 01:10 UTC（北京时间11月20日09:10）发布，修复 `REMOVE_ALL_MESSAGES` 的增量 reducer 和空 checkpoint 处理。它强化状态语义正确性的工程必要性，但不等于外部工具执行 exactly-once。来源：[官方 Release](https://github.com/langchain-ai/langgraph/releases/tag/1.2.24)。

3. **OpenHands 会话产品化（历史对照）。** 官方 `v1.40.0` 于2026-11-12发布，修复历史分页边界和延迟回显覆盖草稿等问题。这属于会话交互一致性，不应推断出执行账本或分布式状态恢复能力。来源：[官方 Release](https://github.com/OpenHands/OpenHands/releases/tag/v1.40.0)。

## 主流路线与 Tradeoff

- **Codex / Harness：** 远程执行与多会话开发体验更灵活；代价是认证上下文、会话生命周期、外部工具副作用必须独立治理。
- **LangGraph / Workflow：** 显式 checkpoint、reducer 和中断恢复可测试性强；代价是版本迁移、状态压缩及工具副作用的业务语义需要自行设计。
- **OpenHands / Sandbox：** 工作区与交互式任务编排方便开发者；代价是多租户隔离、恢复时授权及单位任务资源成本需要生产验证。

## 标准与研究观察

本轮有限检索没有独立核实过去24小时内足以改变 MCP/A2A 标准成熟度判断的正式新规范或可信跨厂商采用数据。MCP 的工具发现、调用授权与执行审计不能混为一项能力；不以兼容声明替代安全或性能验证。

## 7/30天趋势雷达

| 时间窗 | 方向 | 证据判断 |
| --- | --- | --- |
| 7天 | 加强（工程关注） | 远程会话与 checkpoint 正确性仍是近期正式修复的重点；不足以证明规模化采用 |
| 7天 | 待证实 | 跨Worker恢复与外部操作幂等是否形成通用契约，缺独立实测 |
| 30天 | 低置信加强 | Registry 与工具治理分层有AWS官方参考实现，仍缺多厂商生产佐证 |
| 30天 | 待证实 | Sandbox 后端可替换性与统一隔离语义缺可比验证 |
| 30天 | 未见推翻证据 | 不能以未发现新闻认定趋势被推翻 |

## 百万用户 Cloud Agent：可执行建议

优先实现 **Resume Gate + Execution Ledger**：每个 TaskCheckpoint 记录 schema/version、workspace digest、principal、authorization epoch、pending tool operation id；恢复时先校验权限与版本，再查询外部操作状态。对于已派发但回执丢失的非幂等调用，进入 reconciliation，而不是自动重试。用租户级隔离与审计追踪 tool invocation、Sandbox 创建销毁和实际外部副作用。

下周建议建立故障注入矩阵：①升级中旧checkpoint恢复；②撤权后重连；③工具执行成功但响应丢失；④Sandbox重建；⑤流取消与后台任务竞态。分别记录重复副作用率、越权率、恢复P95、单位成功任务成本；这些是建议指标，**不是已测得的benchmark**。

## 情报质量与限制

截至2026-11-23约08:00北京时间，仓库尚无 `intel/daily/2026-11-23.json`。最近可用2026-11-22质量快照：19/19信源抓取成功、59条候选、873条未核验积压；信源抓取成功不等于重要事件覆盖。独立Gold样本数为0，无法计算召回率。研究队列27项为未核验候选，不能自动升级为事实。历史事件库仅2条已核验事件。两条2027-03-31到期预测保持开放，未改条件或概率。KG本期没有充分证据支持实质更新，Delta四组为空。

## 官方 Sources

- [OpenAI Codex alpha.4 Release](https://github.com/openai/codex/releases/tag/rust-v0.173.0-alpha.4)（预发布，2026-11-21 北京）
- [LangGraph 1.2.24 Release](https://github.com/langchain-ai/langgraph/releases/tag/1.2.24)（正式版，2026-11-20 北京）
- [OpenHands v1.40.0 Release](https://github.com/OpenHands/OpenHands/releases/tag/v1.40.0)（正式版，2026-11-12）
- [AWS Agent Registry 官方参考架构](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry/)（历史证据，非今日新品）
