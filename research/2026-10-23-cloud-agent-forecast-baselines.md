---
layout: default
title: "Cloud Agent 的两道架构分水岭：会话授权与可恢复 Workspace"
description: "2026-10-23 一手证据基线、技术路线对比、反证条件与预登记预测"
permalink: /research/2026-10-23-cloud-agent-forecast-baselines/
---

# Cloud Agent 的两道架构分水岭

**研究日：2026-10-23（北京时间）｜定位：技术路线研究，不是当天新闻汇总**

本文回答一个选型问题：百万用户 Cloud Agent 需要将哪些状态视为平台责任，哪些能力应该维持可替换接口？我们把来自不同厂商的一手资料放在同一边界下研究，而不是按照 GitHub Release、PR 或媒体文章的时间顺序排列。

> **核心判断**：工具能被发现，不代表它被安全授权；Sandbox 能暂停并恢复文件，不代表执行步骤能一致恢复。未来竞争的关键是控制面提供什么可验证的契约，而不只是推出更多托管 Agent API。

## 一、当前可核实的技术基线

**发现工具与治理工具存在断层。** AWS 于 2026-10-20 发布的 [Agent Registry 技术文章](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry/) 展示了 Discover → Instantiate → Execute，强调检索到的是批准的能力描述，而不是可以直接用于调用的凭据。这证明能力目录能够与执行客户端分层，但不能证明工具调用已具备跨平台、跨身份的安全闭环。该篇网页发表于 10 月 20 日，RSS 时间为 UTC 10 月 20 日 16:22，即北京时间 10 月 21 日。

更进一步，AWS 的 [Policy Sessions 官方文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-session-based-temporal.html) 描述了工具调用的时序策略：给定 session，可限定调用次数、先后顺序，甚至先读取敏感数据后禁止外传；认证 Gateway 把策略会话与原始调用者 principal 绑定，并在 Gateway → Runtime → Gateway 内部通过服务托管的身份载体传播。**其边界也写得清楚**：跨账户、跨 Region 多跳不受支持；未认证 Gateway 没有按用户隔离的会话保证；Policy Session 并不提供永续工作流状态。

Google Cloud [2026-09-24 MCP Gateway 官方公告](https://developers.googleblog.com/turn-your-rest-apis-into-mcp-tools-with-google-cloud-api-gateway/) 则说明另外一条路线：将 REST API 通过现有 API Gateway 暴露为 MCP 工具，且当时处于 Public Preview。文章确认继承现有 REST 接口验证机制，但**没有据此证明**它已提供与 AWS 相同的跨步骤时序策略和跨 Agent 调用者身份连续性。[MCP Authorization 规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) 说明了授权发现、令牌受众和传输层约束，但规范本身不是上层业务策略、撤销同步或可靠审计已经存在的证明。

**文件可恢复与工作可恢复存在断层。** AWS 的 [AgentCore Runtime 文件系统文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-filesystem-configurations.html) 区分 microVM 的托管 Session Storage（Preview）、Instances 的容量提供者 EBS，以及自带 S3 Files/EFS。microVM 托管 Session Storage 允许停止后以同 session ID 恢复文件，但其文档明示：闲置 14 天后过期，Agent Runtime 版本更新会重置文件。相比之下，Instances 的托管卷可以跨停止保留，[生命周期文档](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-instances-how-it-works.html) 描述最长 14 天的计算会话和卷重新挂载；二者计费、隔离和状态保留边界不同。这里的“恢复文件”没有自动重放 LLM/tool 调用历史的承诺。

执行控制需要另一条保障线。[Temporal 官方 Workflow 文档](https://docs.temporal.io/workflows) 使用持久化 Event History 和 Replay 来重建控制状态，把不可重放的外部 I/O 放在 Activity 中；Worker Crash 后可从历史恢复，既不意味着任意外部副作用真正 exactly-once，也不意味着原 VM 文件系统自动还原。[OpenHands SDK v1.57.0 官方 Release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.57.0) 确认运行环境配置向按会话选择演进，但一个版本发布记录仍不足以证实跨 Worker 热迁移、Workspace 恢复 SLA 或通用 durable replay。

## 二、技术路线竞争不是“谁功能多”，而是谁承担责任

| 能力边界 | 可选技术路线 | 得到什么 | 必须自己验证什么 |
|---|---|---|---|
| Capability Discovery | Registry / MCP Server 清单 / 预编译 Tool Schema | 发现、搜索、升级解耦 | 描述可信度、可用性和调用者是否真正有权 |
| Tool Authorization | 每个 Tool 自授权 / 中央 Gateway + Policy / 代理授权 Broker | 统一身份、准入和审计 | session 绑定、防重放、撤销延迟、跨租户串流 |
| Durable Execution | LangGraph 式 checkpoint / Temporal Event History / 自研 Task 状态机 | 中断恢复与重新调度 | 副作用幂等、checkpoint 粒度、恢复一致性和回放成本 |
| Persistent Workspace | 会话卷 / 自带文件系统 / 外置对象存储 + 按需物化 | 文件与构建产物复用 | 卷删除、版本升级、并发写、成本、完整性 |
| Compute | 微虚机按需唤醒 / 实例长驻 / 混合执行池 | 延迟、隔离和密度之间的选择 | 空闲成本、冷启动、资源配额及故障域 |

三种“session”不可混为一谈：Tool Policy Session 用于授权状态；Agent Task Execution 用于步骤状态与调度；Sandbox Runtime Session 用于计算环境和文件。建议给它们分别建立独立的 ID、生命周期和持久化契约，用 Task ID 关联，但不共用同一失效时间。

### 建议的控制面契约（本站设计分析）

```text
User / Tenant
    │  identity, consent, requested task
    ▼
Task Control Plane ── durable state, retries, HITL, budgets, event trace
    │
    ├── Policy Gateway ── principal, scoped grant, revocation, audit
    │       └── Tool / MCP / A2A call  (idempotency key + policy decision)
    │
    └── Sandbox Scheduler ── lease, resource limits, isolation
            ├── Ephemeral Worker (killable/retryable)
            └── Workspace Store (versioned, separately retained)
```

关键不变量：Worker 丢失不能导致 Task 状态丢失；Workspace 的生命周期不能只靠 Worker 生命周期定义；工具访问必须在执行时校验最新授权，而非仅在 Agent 初始计划时检查；恢复后所有不可重复操作必须具有稳定幂等标识或人工补偿。

## 三、故障窗口与应测假设

| 场景 | 如果简单依赖模型循环或本地盘 | 推荐控制措施 | 可检验指标 |
|---|---|---|---|
| Tool 调用成功、返回前 Worker 崩溃 | 重放会导致二次付款或重复通知 | 工具侧 idempotency key，执行日志记录未知提交状态 | 故障注入后的重复副作用数必须为零 |
| 沙盒升级或重新拉起 | 工作目录可能被清空 | 外部版本化 Workspace，恢复前校验 manifest/hash | 同版本/跨版本恢复成功率与数据校验结果 |
| 会话令牌撤销但 Agent 仍运行 | 继续调用先前发现的工具 | 每次调用 Policy Gateway 校验、授权租约短期化 | 撤销生效尾延迟的 p99，隔离串流为零 |
| 长会话重放历史不断增长 | 控制面重建昂贵甚至超时 | checkpoint/分段 history，事件压缩与继续新实例 | Replay 耗时 p95/p99 与状态一致性 |
| 多 Agent 同时写 Workspace | 同名文件相互覆盖 | 单 writer、per-task 分支、文件版本 CAS | 冲突可检测率与数据损坏次数 |

所有指标都是**推荐测量项目**，本文没有声称某家产品已实现这些结果，也没有制造 benchmark 数字。

## 四、两项正式预测及取舍

### P1 — 工具治理平台的时序授权收敛

预登记 ID：`fc-20261023-tool-policy-session`。截止日 **2027-03-31**。明确检查 Google Cloud API Gateway MCP 与 OpenAI 官方托管 MCP/Agents 工具执行服务两条固定路线，不随结果增减厂商。YES 需要其中至少一个提供正式非 Preview 产品文档，同时满足：调用者身份绑定的会话、两次及以上工具调用之间的时序授权策略、跨 Agent/工具执行节点的原始调用者传播、单次决策审计记录。仅支持 MCP 协议、按请求 JWT 或人工 approval 不算 YES。

主观先验概率 **35%**。其理由不是市场统计，而是 AWS 已显示需求与技术路径，其他厂商出现等价的端到端公开契约仍有集成复杂度和安全边界，Google 目前检索到的 API Gateway MCP 资料标注 Preview。即使 P1 未兑现，也不代表自研 Gateway 的必要性被推翻：它只说明被限定的竞争平台在截止日以前未公开兑现全部指定条件。

工程行动：现在先设计 provider-neutral PolicyDecision 与 PrincipalChain API，不押注单个厂商的 WAT 格式；只有新厂商公开具备相应机制并经故障/授权复核后，才考虑替换本地 Gateway 控制面。

### P2 — microVM 托管 Workspace 的成熟度拐点

预登记 ID：`fc-20261023-agentcore-session-storage`。截止日 **2027-03-31**。只检查 **AWS AgentCore Runtime 的 microVM managed sessionStorage**：YES 需要它脱离 Preview 且官方明确保证在 `runtimeSessionId` 不变的情况下，**Agent Runtime 代码版本更新后仍保留该托管卷数据**，不依靠外置 S3/EFS 或改用 Instances EBS。仅 GA 但升级清空，或仅 Instances 支持跨版本保留，都算 NO。

主观先验概率 **30%**。理由：停止/恢复在现行文档中已具备，但 Preview 退出和跨版本数据迁移是两类不同问题，现有资料明确保留清空限制。这个预测不是 AWS 的上市时间传闻，更不是一般 Storage 能力增速预测。

工程行动：保留可替换 WorkspaceStore 接口，初始优先用对象存储/客户自带持久文件系统存放有业务价值的数据；托管 sessionStorage 只承担有明确过期与升级重置容忍度的临时工作目录。预测 YES 之后也应通过版本升级数据完整性测试，而不是直接解除平台侧双写或备份。

## 五、如何避免预测自我验证

1. **冻结条件**：Git 历史中固定判断和主观概率，不能根据后续新闻修改。
2. **到期不自动裁决**：没有 RSS 消息并不意味着“技术没有发生”。NO 需要复核官方文档和版本历史，YES 需要新的一手核验 Event。
3. **记录负证据**：对于尚未观察到的能力，必须说明检索过哪些官方页面、覆盖的时间窗和不足之处；不能证明全世界不存在。
4. **反馈到选型**：如果 P1 为 NO，则不会因期待托管 Gateway 迅速收敛而推迟自建授权抽象；如果 P2 为 NO，则继续维持独立 Workspace 持久化预算与迁移能力。
5. **不给少样本打分**：两项预测在登记时没有结果，不显示“预测成功率”；至少五个真正独立判定的二元结果之后才尝试 Brier 均值，仍须说明样本偏差。

**证据性质**：AWS、Google、Temporal、OpenHands、MCP 的上述官方文档为事实来源；设计矩阵和先验概率为本研究的推断与决策假设。厂商文档会更新；未来复核必须保存观察日期并明确哪些结论属于当时的公开状态。
