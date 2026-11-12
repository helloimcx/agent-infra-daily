---
layout: post
title: "Agent Infra Daily｜2026-11-13：流式工具调用与运行时执行语义的边界"
date: 2026-11-13 08:00:00 +0800
summary: "Codex 0.167.2 的 Vertex AI 增量工具更新提示协议适配层的重要性；预发布不代表生产能力，百万用户 Agent 应分离流式传输、工具提交和执行账本。"
tags: [agent-infrastructure, codex, tool-governance, durable-execution, cloud-agent]
---

## 今日核心判断

**流式工具调用是交互与传输层优化，不等于工具调用已提交、外部副作用已完成或任务具备可恢复性。** 近24小时的一手来源检索没有找到足以认定新的 P0 级生产架构或行业标准正式发布的证据。今天以已核验的正式补丁和预发布边界为切入点，比较 Agent 运行时的三个不同状态层。

## 重要进展与证据边界

### 1. Codex 0.167.2：Vertex AI 工具更新增量发送

OpenAI Codex 官方 [0.167.2 release](https://github.com/openai/codex/releases/tag/rust-v0.167.2) 标记为正式版；GitHub 显示发布于 2026-11-11 22:44 UTC，即北京时间 11 月 12 日 06:44。Release Notes 明确表示，面向 Google Cloud Vertex AI 的工具更新默认增量发送，并提供 `incremental_tools_legacy_gcp` 配置开关。该更新表明 Provider 协议适配仍需处理流式工具事件的兼容性，但不能据此推断服务端业务操作幂等或任务恢复性能已经改善。官方未披露相关延迟、可靠性 Benchmark。

### 2. Codex 0.170.0-alpha：仍为预发布

[Codex Releases](https://github.com/openai/codex/releases) 显示 0.170.0-alpha.2 / alpha.3 / alpha.4 在北京时间 11 月 12 日至 13 日出现；它们均标记为 Pre-release，简要说明不足以确认新的生产级 Agent 恢复能力。尤其不能将版本号迭代解释为标准成熟度或部署采用率的证据。

### 3. Anthropic Sandbox Runtime：隔离和网络治理仍有显式边界

[官方 Sandbox Runtime](https://github.com/anthropics/sandbox-runtime) 文档区分网络 allowlist、外部决策代理和 per-command allowlist；后者依赖调用标识，官方明确提示它不是同一会话内并发命令之间的安全边界。此前正式版 0.0.82 的 Windows 权限收紧是历史证据，不是今天的新发布。它提醒我们：执行隔离与工具级授权不能混为一谈。

## 主流路线与 Tradeoff

- **Codex / Provider adapter**：增量传输改善事件交互潜力，但增加乱序、半包、重连和兼容性测试复杂度。
- **LangGraph / durable orchestration**：Checkpoint 和严格恢复可以约束执行状态；对外部副作用仍须独立去重和对账。
- **Sandbox / policy gateway**：系统调用、文件、网络隔离缩小风险面；动态授权、租户撤权与审计仍需独立可信控制面。

## 标准与研究

本次未核实到过去约24小时正式发布、且实质改变 MCP/A2A 互操作或 Agent durable execution 语义的新标准。MCP 工具发现、工具授权、执行回执、任务恢复应作为不同契约评估；不能把规范支持等同于实际的跨厂商互操作证明。

## 7 / 30 天趋势雷达

- **7天加强（有限证据）**：Provider 流式工具事件兼容性持续迭代；取消、恢复、授权重检的工程问题反复出现。
- **30天加强（低置信）**：工具 Registry 与 Gateway 的职责分离；仓库已有 AWS 一手参考架构事件作为有限支持。
- **待证实**：跨 Provider 的无损任务迁移、共享 Sandbox Supervisor 的大规模可靠性、模型线程缓存的持久化能力。
- **推翻**：本期没有达到可推翻长期趋势的独立反证。

## 百万用户 Cloud Agent 的具体建议

为工具调用引入四阶段状态：`streaming`（模型仍在生成参数）→ `validated`（完整参数和授权验证通过）→ `dispatched`（已持久化操作意图并发送）→ `reconciled`（收到外部系统可核实回执）。以 `tenant_id/task_id/operation_id/attempt_id` 关联事件、幂等键和审计；断线恢复只重放**事件流**，不自动重放已派发的副作用。先用 1% 灰度验证断流、参数截断、跨 Provider 切换、外部成功但响应丢失四类故障。监测重复操作数、越权次数、p95/p99 TTFT、恢复成功率和单位成功任务成本；不预设收益。

## 情报质量与知识图谱

截至本次读取，`intel/daily/2026-11-13.json` 尚不存在。最近的 11 月 12 日质量快照显示 19/19 信源成功抓取、83 条当期候选、582 条跨日未核验候选；独立 Gold 样本为 0，重要事件召回率不可计算。抓取成功不代表覆盖完整。长期 KG 没有足够新证据触发实体级实质更新，今日 Delta 四组均为空。两项 2027-03-31 到期的登记预测保留原有条件和概率，不提前裁决。

## 官方 Sources

1. [OpenAI Codex 0.167.2 正式版](https://github.com/openai/codex/releases/tag/rust-v0.167.2)
2. [OpenAI Codex Releases（Alpha 状态）](https://github.com/openai/codex/releases)
3. [Anthropic Sandbox Runtime 官方文档](https://github.com/anthropics/sandbox-runtime)
4. [AWS Agent Registry 参考架构（历史证据）](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry)
