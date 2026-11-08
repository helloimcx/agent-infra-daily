---
layout: post
title: "Agent Infra Daily｜2026-11-08：恢复语义的安全边界与周度证据审阅"
date: 2026-11-08 08:00:00 +0800
summary: "过去约24小时未确认新的P0级正式发布；从LangGraph严格恢复与Agent工作台更新提炼执行控制面边界，披露周审计覆盖缺口。"
tags: [agent-infrastructure, durable-execution, security, cloud-agent, weekly-review]
---

## 今日核心判断

**恢复执行的正确性，比单纯提高恢复成功率更重要。** 截至北京时间11月8日08:00左右，本次独立检查的官方版本记录中，没有确认过去约24小时出现新的P0级正式生产能力或标准。以下为已核实的近一周证据回顾，不把历史版本冒充今日新发布。

## 重大进展与证据边界

### 1. LangGraph：严格恢复拒绝过期的人机交互答案

[LangGraph 官方 Releases](https://github.com/langchain-ai/langgraph/releases)记录：11月5日发布的 langgraph 1.2.20 为任务内每次 interrupt() 分配独立ID，并引入 strict resume，拒绝陈旧 interrupt 答案；11月6日发布的 Python SDK 0.4.14 将 strict_resume 暴露到 runs.create、stream 和 wait。该机制减少旧审批答案误用于新暂停点的风险，但不等于跨进程业务操作自动恰好执行一次。上述发布日期均早于今日观察窗口。

### 2. LangGraph JS：重连与副作用重试进一步收紧

[LangGraph.js 官方 Releases](https://github.com/langchain-ai/langgraphjs/releases)显示，11月5日的 SDK 1.13.0 修复切换线程后重复执行待处理工具，以及可能已送达服务器的 POST/PATCH 请求被自动重试的问题；并补充取消原因和结束事件状态。这是具体的客户端恢复语义改进，不代表所有下游工具具备幂等性。

### 3. OpenHands：SDK/Agent Server 与自动化控制面分层

[OpenHands SDK 仓库官方说明](https://github.com/OpenHands/software-agent-sdk)区分了 SDK/Agent Server 的会话执行、事件、工作区和 REST/WebSocket 接口，以及 automation 仓库负责的调度、Webhook、运行历史和派发。这是架构职责边界，不是本日的新产品公告；没有可独立验证的百万用户吞吐或恢复SLA。

## 主流路线与 Tradeoff

LangGraph 强化应用层状态机、interrupt ID 和恢复协议，优势是可精细控制业务流程，但调用者仍需管理外部副作用与授权；OpenHands 将会话执行服务与自动化调度解耦，适合构建独立控制面，但跨层一致性和故障恢复需要自行验证；Sandbox 类方案强调隔离与资源管理，不能替代持久化业务账本。三者不是同一层面的直接性能竞品。

## 标准与研究

本轮未发现足以改变选型的全新正式标准。MCP 工具描述和注解不应被当作可信授权；对于高风险工具，必须在服务端按真实调用主体执行策略判定，并记录决策依据。尚无独立证据证明某一种方案已经成为通用生产标准。

## 7/30天趋势雷达

- **加强（7天）**：任务恢复与取消传播的细粒度语义；LangGraph Python/JS 官方版本提供相互独立的实现证据。
- **加强但待规模验证（30天）**：Agent 工作台、执行服务、Sandbox 和工具网关控制面分层；官方设计与版本迭代增加，但缺乏跨厂商同口径基准。
- **待证实**：共享 Supervisor 的生产高可用、跨后端无损会话迁移、百万用户下的单位成功任务成本。
- **尚无证据推翻**：外部业务副作用应由独立幂等账本治理的工程假设。

## 百万用户 Cloud Agent：本周建议落地的验证

实现 `Resume Authorization Fence`：每次从 checkpoint 恢复时核对 tenant/user/agent/task、权限版本、预算余额、审批 interrupt ID 和执行截止时间；拒绝过期审批。将 `Execution Ledger` 与上下文缓存分离，使用操作ID、幂等键、外部回执和终态去重。故障注入至少覆盖：断线重连、旧审批重放、外部操作成功但响应超时、执行中撤权、跨线程切换。量化重复副作用次数、越权次数、恢复p95/p99和单位成功任务成本，不预设结果。

## 周日独立信源审阅与质量边界

今日 `intel/daily/2026-11-08.json` 在本次读取时不存在。最近快照（11月7日）显示19/19信源抓取成功、75条当期候选、453条跨日未核验候选；Gold有效样本为0，**无法计算召回率**。已独立查看 LangGraph Python/JS 官方 Release，相关版本能从一手记录确认，但这只是有限抽查，不能称为全面漏报审计。候选队列并非已核验事件，Sitemap lastmod不是发布日期。既有2条已登记预测均于2027-03-31到期，保持原条件、概率与未决状态。

## 官方 Sources

1. [LangGraph Python Releases](https://github.com/langchain-ai/langgraph/releases)
2. [LangGraph.js Releases](https://github.com/langchain-ai/langgraphjs/releases)
3. [OpenHands Software Agent SDK](https://github.com/OpenHands/software-agent-sdk)
