---
layout: post
title: "Agent Infra Daily｜2026-11-09：恢复语义与授权边界的生产化检验"
date: 2026-11-09 08:00:00 +0800
summary: "过去约24小时未核实新的P0正式发布；以近期LangGraph严格恢复、AWS身份治理和Codex会话工作台为对照，明确恢复、授权与外部副作用的分层契约。"
tags: [agent-infrastructure, durable-execution, security, sandbox, cloud-agent]
---

## 今日核心判断

**过去约24小时内，独立检索尚未确认值得升格为P0的全新正式产品、架构或标准发布。** 近期一手材料共同揭示一个更重要的生产约束：Agent 的会话恢复、审批有效性和外部业务操作不能共用一个“恢复成功”布尔值。恢复任务时必须重新确认权限，并独立对账已经发生的副作用。以下列举的是历史证据与当日判断，**不是将旧公告冒充今日新品**。

## 近期三项进展与证据边界

### 1. LangGraph严格恢复：拒绝过期的人工审批答案

LangGraph 1.2.20（官方Release标注11月5日）为每次任务中 `interrupt()` 赋予独立ID，新增拒绝过期答案的 strict resume；Python SDK 0.4.14（11月6日）将 strict_resume 暴露给 runs.create、stream、wait。它改善的是**执行状态与人类输入的匹配**，不是对支付、邮件、文件修改等外部操作提供 Exactly-once 保证。来源：https://github.com/langchain-ai/langgraph/releases

### 2. AWS AgentCore + Okta：身份委托与执行策略分层

AWS 11月6日官方技术文章《Govern AI agent access with Okta Cross App Access and Amazon Bedrock AgentCore – Part 2》描述：AgentCore Gateway 作为工具入口，兑换 Okta 授权，Cedar 策略绑定工具与 Agent，另一 Agent 运行于 EKS，并将允许/拒绝记录关联到可观测性体系。这是**厂商参考实现/技术教程**，并非跨厂商标准或百万用户生产压测。来源：https://aws.amazon.com/blogs/machine-learning/

### 3. Codex工作台与Sandbox：会话切换不等于状态迁移

Codex 0.167.0正式版（11月6日）改善多后端会话管理、草稿保留和网络审批交互；NVIDIA OpenShell 0.1.7（11月4日）改善共享Supervisor恢复和审计，但共享Supervisor仍是实验能力。前者优化用户交互和后端选择，后者优化执行隔离；两者均不足以证明跨后端任务、授权与Workspace能无损迁移。来源：https://github.com/openai/codex/releases 与 https://github.com/NVIDIA/OpenShell/releases

## 主流路线与Tradeoff

- **工作台/Harness路线（Codex）**：会话切换与人工审查体验更好；跨执行后端的Checkpoint兼容性、权限重检仍需平台实现。
- **Durable Graph路线（LangGraph）**：状态/中断/恢复语义明确；外部副作用、租户授权与预算账本不应直接托付给Graph Checkpoint。
- **托管Gateway/身份路线（AWS AgentCore）**：集中发现、授权、审计便于企业治理；跨云可移植性、策略复杂度和额外调用路径成本需要测量。
- **Sandbox路线（OpenShell）**：隔离执行与共享Supervisor有资源效率潜力；故障域、冻结时间和实验性能力限制了直接规模化推断。

## 标准与研究

MCP工具描述与注解不能被视为可信授权决策；当前未确认过去24小时内有改变这一边界的正式标准修订。研究与工程上应区分三种可验证性质：**恢复到正确状态、重新取得当前授权、避免重复外部副作用**。不将GitHub讨论、预发布或Sitemap更新时间等同于正式发布。

## 7/30天趋势雷达

| 方向 | 7天 | 30天 | 证据边界 |
| --- | --- | --- | --- |
| 恢复与审批状态绑定 | 加强 | 加强 | LangGraph正式版有具体语义，缺少跨实现规模验证 |
| 工具授权与身份治理 | 加强 | 加强（低置信） | AWS等一手架构案例；不能推导行业采用率 |
| Sandbox与持久Workspace解耦 | 待证实 | 待证实 | 不同项目路线互补，缺少统一契约 |
| 多后端无损会话迁移 | 待证实 | 待证实 | UI切换不等于Checkpoint迁移 |
| 已被推翻的重大趋势 | 无新增 | 无新增 | 证据不足时不强行给出结论 |

## 百万用户Cloud Agent：本周可执行工程建议

建立 **Resume Authorization Fence + Execution Ledger** 的最小跨服务契约：

1. **Checkpoint** 记录 task_id、workflow_version、resume_cursor、workspace_commit、pending_approval_id；不可将短期模型Thread ID作为唯一恢复点。
2. **Authorization Fence** 每次恢复/执行前按 tenant_id、principal_id、delegation_id、policy_version、expires_at 重新校验；撤权后历史审批立即失效。
3. **Execution Ledger** 对每个副作用操作生成稳定 operation_id/idempotency_key，记录 prepared、dispatched、acknowledged、unknown、reconciled 状态与外部回执。响应超时进入 unknown 并查询外部状态，不能盲目重试。
4. **故障注入**：客户端断线、审批过期、执行中撤权、Sandbox替换、外部操作成功但回执丢失；观察重复副作用次数、越权次数、恢复p95/p99和每成功任务成本。上述均为待测指标，不是已有Benchmark。

## 信源健康、预测与知识图谱

截至研究时，`intel/daily/2026-11-09.json` 尚不存在；最近的11月8日质量快照：19/19信源抓取成功、64条候选、454条跨日未核验候选。抓取成功不等于重大事件覆盖，候选不等于核验事实；独立Gold样本为0，无法计算有效召回率。研究队列积压需单独治理。现有2条长期预测均未到期（目标2027-03-31），不修改原始条件/概率，也不提前判定。无足够证据触发长期KG实质更新，Delta四组空数组。

## 官方Sources

- LangGraph Releases：https://github.com/langchain-ai/langgraph/releases
- AWS Machine Learning Blog（2026-11-06 Okta/AgentCore Part 2）：https://aws.amazon.com/blogs/machine-learning/
- Codex Releases：https://github.com/openai/codex/releases
- NVIDIA OpenShell Releases：https://github.com/NVIDIA/OpenShell/releases
