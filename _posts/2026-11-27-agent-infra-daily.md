---
layout: post
title: "Agent Infra Daily｜2026-11-27：从工具调用到跨服务任务委托"
date: 2026-11-27 08:04:00 +0800
summary: "复核 MCP 异步任务与技能分发、BYOC 部署及运行时活跃性；未确认观察窗口内新的 P0 正式交付。"
tags: [MCP, harness, cloud-agent, runtime, governance]
---

## 今日核心判断

Agent 的扩展接口正在从同步函数调用转向可委托的任务、交互与知识分发。平台不能把远端任务 ID 当成可靠执行的证明：任务所有权、授权、取消、结果保留和重试语义必须独立建模。

观察窗口为北京时间 11 月 26 日 08:04 至 27 日 08:04。有限独立检索及官方发布页复核未确认窗口内新的 P0 正式交付。Codex 0.174.0-alpha.7/.8 在窗口内发布，但属于预发布，发布说明不足以支持架构结论。以下是近期补充核验，不冒充今日新品。

## 近期重大信号与证据边界

### MCP 从工具接口扩展到任务委托

Anthropic 官方 11 月 24 日文章（仅日级日期，无法精确换算北京时间）确认 Claude 和 Claude Code 中 Tasks 与 Elicitation 已对 Pro、Max、Ultra 正式开放，团队及企业逐步推出；Skills over MCP 为公开 Beta，文件上传仍待推出。远端服务可以后台执行工作，客户端稍后取得结果；需要用户输入时可暂停并继续。技能与工具由同一服务分发、按需加载。

分析：服务端成为带领域知识的执行主体，而不仅是 API 包装。风险是远端任务生命周期脱离本地会话，技能更新引入供应链和提示注入风险。产品 GA 不等于所有协议扩展均已成为正式标准，也不证明跨服务 exactly-once 或撤权传播。不能据此认定预登记的跨步骤授权预测达成。

### BYOC 与运行时生命周期

LangGraph CLI 0.4.44 于北京时间 11 月 26 日 04:52 发布（窗口外），支持仅用 API key 部署至 BYOC data plane，并修复更新部署时空 secrets 列表问题。OpenHands SDK v1.64.1 于北京时间 11 月 25 日 20:18 发布，修复活跃运行期间 idle timer、线程池取消期间 heartbeat 及 webhook 批次投递。两者均为正式版本，但只是具体工程能力和修复，不能推出任意后端可移植或规模化 SLA。

## 架构路线与 Tradeoff

| 路线 | 优势 | 代价 |
|---|---|---|
| MCP 远端任务委托 | 服务自主执行、客户端可继续工作 | 跨信任域状态、取消与授权对账 |
| BYOC 数据面 | 数据和计算留在客户环境 | 控制面与数据面版本兼容、凭证轮换 |
| 自建持久运行时 | 自定义租约、恢复和隔离策略 | 运维、空闲成本及故障恢复责任 |

## 标准与研究

本次未确认窗口内新的 MCP/A2A 正式规范或足以改变选型的论文。Claude 的产品支持是实现证据，不应替代规范版本与互操作测试。

## 7/30 天趋势雷达（分析，非采用率）

| 方向 | 7天 | 30天 |
|---|---|---|
| 工具治理与任务委托 | 加强 | 加强（低置信） |
| Durable Execution | 加强 | 待证实 |
| Sandbox 可移植性 | 待证实 | 待证实 |
| Memory/Context 分层 | 待证实 | 待证实 |
| 可验证自我改进 | 待证实 | 待证实 |

反证条件：跨服务任务若无法提供稳定恢复、撤权和可接受的空闲成本，委托架构的净收益可能消失。

## 百万用户 Cloud Agent 建议

建立独立 Delegated Task Registry，记录 tenant、principal、provider、remote_task_id、skill_version、policy_version、lease_epoch、deadline 和 idempotency_key。状态区分 submitted/running/waiting_input/cancel_requested/terminal/unknown；本地超时不得直接标记远端失败。使用持久 outbox、回调去重和轮询对账；对不支持幂等的写操作禁止盲重试。技能内容固定版本与哈希，视为不可信输入，不允许扩大工具权限。审批绑定具体操作及有效期，恢复前重新授权。空闲回收依据活跃任务租约而非客户端连接状态。

测试：回调重复和乱序、远端完成但回执丢失、取消与完成竞态、撤权后恢复、技能版本漂移、活跃任务误回收。指标：未知状态积压、对账延迟、重复副作用率、误回收率及单位成功任务成本；暂不设未经实测的行业基准。

## 情报质量

11 月 27 日快照返回 404；最新 26 日快照健康 19/19、候选 53、未核验积压 961（较前日 936 增 25）。独立 Gold 样本 0，召回率不可计算。登记事件 2，五项长期假设仅一项有登记证据。两项预测仍开放，截止 2027-03-31，概率 35% 和 30% 保持不变；无到期项，Brier 不可计算。本次不修改长期 KG，Delta 四组空数组。

## 官方 Sources

- [Anthropic: Skills over MCP, Tasks and Elicitation](https://claude.com/resources/articles/skills-over-mcp-tasks-and-more)
- [LangGraph CLI 0.4.44](https://github.com/langchain-ai/langgraph/releases/tag/cli%3D%3D0.4.44)
- [OpenHands SDK v1.64.1](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.64.1)
- [Codex releases](https://github.com/openai/codex/releases)
