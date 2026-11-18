---
layout: post
title: "Agent Infra Daily｜2026-11-19：恢复正确性与沙盒升级安全成为共同约束"
date: 2026-11-19 08:00:00 +0800
summary: "OpenAI Agents SDK、Codex 与 NVIDIA OpenShell 的正式版本分别揭示 Checkpoint 兼容、授权竞态及沙盒升级风险；建议以版本化执行契约贯穿恢复、授权与迁移。"
tags: [agent-infrastructure, cloud-agent, sandbox, durable-execution, security]
---

## 今日核心判断

**Agent 运行时的关键竞争点正从单纯“可恢复”，延伸到升级、撤权、跨工作进程迁移之后仍然保持正确性。** 过去约24小时确认三项官方正式版本（均非预览），它们独立触及状态序列化、授权竞态、沙盒网络边界和升级迁移。不能据此推断跨产品统一标准已形成，也没有独立百万用户基准。

## 三项重要进展及证据边界

### 1. OpenAI Agents Python SDK v0.25.0：Checkpoint 兼容与沙盒迁移（北京时间11月18日08:22）

官方发布说明移除了 beta Runloop Sandbox Provider，提醒使用者迁移前保存 Workspace，Provider 专属 Session/Snapshot 需要单独迁移。RunState 1.22 改善嵌套 Agent 工具审批恢复和 Pydantic 默认值、原地修改的保存；跨 Worker 共用 Checkpoint 的系统应先升级读取端。MCP v2 Streamable HTTP 支持并发请求。**边界：**这是 SDK 版本契约和迁移要求，不代表所有对象都可序列化，进程内资源仍需自定义 Serializer，也不代表跨 Provider 自动恢复。

来源：https://github.com/openai/openai-agents-python/releases/tag/v0.25.0

### 2. Codex 0.170.0：会话重连、权限与 OAuth 竞态修复（北京时间11月18日11:40）

正式版改进 Cloud 会话自动重连，保留恢复中的活动 Turn；修复 MCP OAuth 在取消、登录和退出时的凭证竞态，修复子线程丢失 Sandbox 限制、权限更新和 Windows 文件替换问题。实验性同名 MCP Server 跨环境支持仍不能视为稳定承诺。**边界：**修复清单不能证明外部工具 Exactly-once 或生产故障恢复 SLA。

来源：https://github.com/openai/codex/releases/tag/rust-v0.170.0

### 3. NVIDIA OpenShell v0.1.9：隔离策略和升级数据库风险（北京时间11月18日03:12）

正式版收紧通配符网络策略：私有 IP 不能仅凭 wildcard endpoint 放行，需明确 endpoint 或 allowed_ips。Postgres Gateway migration 010 使用普通 CREATE INDEX，会阻塞 objects 表写入，升级大型部署须规划维护窗口。另调整 Helm metrics 配置、Go SDK 路径及 HTTP Middleware Hook。**边界：**安全收紧可能破坏既有策略，升级需预检；发行说明不等于多租户性能实测。

来源：https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.9

## 主流路线与 Tradeoff

- **SDK / Framework 路线（Agents SDK、LangGraph）**：Checkpoint 与人工审批贴近 Agent 逻辑，开发集成便利；但序列化格式、Provider Snapshot、业务副作用的责任边界仍需应用明确。
- **Coding Agent 工作台（Codex）**：重点改善连接恢复、交互和权限一致性；但会话重连不等于跨执行后端完整状态迁移。
- **隔离运行时（OpenShell）**：更明确的网络策略、Gateway 和升级契约；代价是运维迁移、策略兼容性及共享组件故障域。

## 标准与研究观察

本次没有确认 MCP/A2A 在该24小时窗口内发布新的正式规范。MCP v2 并发能力是具体 SDK 的实现信号，不能等同协议层跨租户授权或工具幂等的保证。独立研究仍缺少跨 Provider 恢复、撤权与副作用对账的可复现实测对照。

## 7/30天趋势雷达（定性判断，非采用率）

- **加强（7天）**：会话/任务恢复正确性、取消与 OAuth 竞态处理；来自多个独立官方版本的修复方向。
- **加强（30天）**：Sandbox 策略、执行审计、可替换 Compute Backend 的工程关注度；不代表跨后端语义已经统一。
- **待证实（7/30天）**：Checkpoint 格式的跨框架兼容、百万用户下的恢复成本和共享 Gateway 故障域。
- **未观察到明确推翻证据**：长期状态与外部执行分层的架构假设；证据不足以提高已登记预测概率。

## 百万用户 Cloud Agent：下一步可落地工程

优先实现 **Versioned Resume Contract**：持久化 task_id、checkpoint_schema_version、workspace_manifest_hash、provider_id、principal_id、auth_epoch、tool_call_id、idempotency_key 与外部操作状态。恢复顺序为“校验 Schema/Workspace → 重新认证授权 → 对账未决 Tool Call → 继续调度”。对不兼容 Checkpoint 拒绝静默恢复，对未知结果的外部写入禁止直接重试。

上线前建立四类故障注入：跨 Worker 滚动升级、撤权与取消并发、Sandbox 网络策略升级、Postgres Gateway schema migration 期间持续写入。指标包括恢复正确率、重复副作用率、越权调用数、升级写阻塞时长及每成功任务成本。所有数值由内部压测获得，不能套用厂商发布说明。

## 信源与研究质量

截至本次读取，2026-11-19 的采集快照尚不存在；最近的 2026-11-18 快照有19/19信源成功、77条当期候选、744条跨日未核验积压。独立 Gold 样本为0，重要事件召回率不可计算。候选和 Sitemap lastmod 均不视作已核实事件。两项到期日2027-03-31的预测仍保持原始条件与概率，未提前判定。

## 官方 Sources

1. OpenAI Agents Python SDK v0.25.0：https://github.com/openai/openai-agents-python/releases/tag/v0.25.0
2. OpenAI Codex 0.170.0：https://github.com/openai/codex/releases/tag/rust-v0.170.0
3. NVIDIA OpenShell v0.1.9：https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.9
4. LangGraph 严格恢复历史对照：https://github.com/langchain-ai/langgraph/releases
