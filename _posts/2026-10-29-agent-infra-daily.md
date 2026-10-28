---
layout: post
title: "Agent Infra Daily｜2026-10-29：Sandbox身份默认拒绝、Supervisor池化与Agent预算治理"
date: 2026-10-29 08:00:00 +0800
summary: "复核NVIDIA OpenShell v0.1.6、OpenHands SDK v1.59.0和Codex v0.165.0：Agent基础设施的生产门槛正集中在身份默认拒绝、隔离执行恢复、共享Supervisor容灾、会话预算和可审计工具边界。"
tags: [agent-infra, cloud-agent, sandbox, durable-runtime, harness, security, multi-tenant, agentops]
---

## 今日核心判断

**Agent Infra 的近期实质进展，不是让模型多调用几个工具，而是把身份、沙盒控制连接、恢复语义、成本预算和审计从模型循环中独立出来。** 本次独立检查NVIDIA OpenShell、OpenHands、OpenAI Codex、LangGraph的官方GitHub Release，并对照OpenAI Agents API、AWS AgentOps及Anthropic一手公告。**最有生产启示的变化来自OpenShell v0.1.6：网关认证默认拒绝、沙盒主动建立控制通道、实验性共享Supervisor和显式的恢复失败语义。** 但共享Supervisor仍属实验性，不能将功能存在视为经过百万用户压测。

时间核验：OpenShell v0.1.6的GitHub Release发表于UTC 2026-10-27 17:56:58，即北京时间**10月28日01:56**，略早于严格的过去24小时窗口，仍纳入约30小时架构观察；OpenHands v1.59.0发表于UTC 10月28日14:34:44，即北京时间**10月28日22:34**，属于过去24小时。Codex v0.165.0发表于UTC 10月27日20:09:38，即北京时间**10月28日04:09**，作为近30小时对照。日期来自官方Release记录，不用RSS抓取时间冒充发布时刻。没有确认新的跨厂商正式标准或可复验的百万用户性能基准。

## 一、重大进展及证据边界

### 1. NVIDIA OpenShell v0.1.6：Sandbox安全与控制面进入可操作的产品设计

**已核验｜官方稳定版Release，10月28日01:56（北京）。** 网关现在默认要求OIDC、mTLS用户/运维身份或网关JWT；若缺少认证配置则拒绝启动。仅受信任的本地开发可显式设置allow_unauthenticated_users。与“部署后再补鉴权”相反，这是一种**安全默认值**：错误配置应导致启动失败，而不是开放未认证的沙盒入口。

新建Kubernetes、Docker、Podman、VM沙盒改为**从沙盒向Supervisor主动建立控制连接**。官方要求Supervisor与Sandbox运行时二进制一起升级；旧版拒绝新沙盒。对多云、NAT、动态网络与租户隔离有设计价值，但并不意味着所有网络拓扑自动兼容，也不证明现有连接无需迁移。

**Suspend/Resume正式进入CLI和SDK能力表，但取决于compute driver。** 不支持的驱动会返回unimplemented；外部隔离后端的ResumeBoundaryRequest字段语义也有变化。不能把“支持恢复API”理解成所有驱动均支持完整进程、内存、网络连接恢复，更不能理解为业务副作用exactly-once。需要定义restore失败时究竟返回错误、重启还是人工接管，并保存可追溯的恢复原因。

**实验性共享Supervisor：** Kubernetes可用supervisor_topology=gateway让一个进程监督多个沙盒，Supervisor池可接管故障成员的沙盒；但一副本没有即时冗余，接管时工作负载可能短暂冻结，已有代理连接和交互会话必须重连，超过恢复期限仍可能终止。这是“共享控制面降低单位租户开销”与“故障域扩大”之间的真实Tradeoff，尚非已证明的生产SLA。

**审计与策略：** 网关开始以OCSF记录授权拒绝、已接受凭据、SSH会话令牌和沙盒令牌检查，并对疑似凭据误用给出高严重度发现；中间件binding_policy可限制必需的请求检查绑定，但旧Supervisor不强制执行该策略。上线应执行兼容性矩阵，防止策略配置已生效而旧运行时实际绕过。

### 2. OpenHands software-agent-sdk v1.59.0：从Skill装载走向会话预算和ACP能力契约

**已核验｜官方稳定版Release，10月28日22:34（北京）。** 新版本支持Agent Server为单个conversation设置、更新成本预算，并让SDK客户端读取、追踪预算；ACP Agent可通过文件与路径目录暴露Skills，修复了客户端传入Skill丢失、Skill来源子路径、MCP OAuth回调重放等问题。它们共同说明，Skill不只是提示词文本，还涉及**路径来源、生命周期、权限与消费额度**。

**工程边界：** 发布说明仅证明这些API/修复已合入该版本，不证明跨ACP实现的统一兼容性，也未给出预算硬切断在并发请求、流式输出、模型重试时的强一致保证。若成本预算是财务或安全硬边界，必须在调用前预留额度、在网关做并发配额仲裁，并在完成后对账；只在Agent内部读取预算值不足以防超支。

### 3. Codex v0.165.0：多环境Provider、记忆迁移与MCP取消语义的近30小时对照

**已核验｜官方稳定版Release，10月28日04:09（北京），非严格过去24小时新增。** 新增内置Google Cloud Vertex AI provider；新建profile默认使用memory v2，并支持外部Agent记忆导入；app-server加入**实验性**附着式thread forks；修复本地等待方取消后远端MCP请求未取消的问题，及中断/切换Plan模式后排队消息错误唤醒执行的问题。这里最值得借鉴的是**取消传播与执行唤醒条件**：长任务恢复不应在用户撤销、任务终止或权限变化后意外继续。

这些属于客户端/运行时功能与修复，不能直接推出托管Sandbox的生产级持久化或跨厂商统一记忆标准。实验性thread forks也不等于通用的分支合并冲突处理协议。

## 二、主流路线与架构Tradeoff

**NVIDIA OpenShell：** 自管或可移植Sandbox执行面 + Gateway/Supervisor + 驱动层；优势是隔离策略、控制链路、部署形态和审计可直接工程化；代价是版本协同、驱动适配、控制面高可用与故障恢复的自有运维责任。共享Supervisor能摊薄常驻控制进程，但必须量化单Supervisor故障影响的沙盒数量。

**OpenHands：** SDK/Agent Server/ACP围绕可扩展Agent与Skill生态，重视客户端能力、会话预算与工具接入。适合混合Agent实现；代价是多Agent协议语义、Skill来源信任、OAuth凭据与成本控制必须另行治理。

**OpenAI Agents API（9月10日公开测试版，历史背景）：** 托管Codex Harness与可选择的Sandbox环境分离，减少自行维护循环和上下文压缩的成本，但对托管边界、版本行为、数据驻留和可观测出口存在依赖。其public beta不能写成全面GA。**AWS AgentCore（既有GA服务）**强调Runtime、Identity、Gateway、Memory与AgentOps的模块化部署；服务整体成熟度不代表某个Session Storage Preview特性已GA。

架构建议不是三选一：将**任务控制面**（身份、策略、预算、事件日志、checkpoint、恢复决策）与**执行面**（容器/microVM/浏览器/远端工具）解耦，以适配不同成本与安全等级的用户任务。

## 三、标准与研究：不把协议发布误当成安全证明

**MCP/ACP/Skills是不同层面的互操作接口**：工具调用、Agent通信/客户端能力、任务知识封装各有边界；没有任何一个协议天然解决跨租户授权、成本预算、可审计恢复或工具副作用幂等。OpenHands的ACP Skill目录与NVIDIA的binding_policy是具体实现信号，而非跨生态合规认证。

Anthropic于**10月28日**发布AI for Science合作扩展公告，提到20家科研机构/组织及Model Hardware Standard（MHS）；但MHS最初公开是**8月27日research preview**，不是10月28日新发布的GA标准。其硬件driver以read/write原语、设备发现与安全边界连接Agent，仍需专家监督。对通用Cloud Agent的启示是：模型可以规划，执行器必须有独立、确定性的安全限制。科研合作扩展不应被误报为Agent Infra的生产标准突破。

本次未检索到可独立重现的最新大规模Sandbox隔离或Supervisor故障接管Benchmark。GitHub发行说明是第一手版本事实，但性能、安全有效性仍须自行测试。

## 四、7天／30天趋势雷达

**7天·加强（中等方向性，非采用率）：** Sandbox默认认证、会话审计、预算控制、恢复API、可追踪Skill来源在多个独立项目出现。OpenShell与OpenHands的官方稳定版给出直接实现证据。

**7天·待证实：** 实验性共享Supervisor在10万级沙盒下的成本与故障域收益；不同compute driver的Suspend/Resume恢复一致性；会话预算在并发重试和中断情况下能否做到硬限额。

**30天·加强但置信度有限：** Harness与Sandbox可分离、Registry/Policy与调用执行分层、长任务状态脱离单次模型上下文的架构方向。历史OpenAI Agents API和AWS AgentOps支持这些方向，但未构成全行业普遍采用的证明。

**30天·减弱/警示：** “有SDK恢复接口就等于Durable Execution”的推断受到驱动未实现、控制链路重连和故障接管期限限制的反证；“共享Supervisor天然更高可用”也不成立。

**推翻条件：** 若真实故障注入显示共享Supervisor比每沙盒独立监督带来更高用户可见失败率，或恢复依赖无法满足业务RPO/RTO，应回退到隔离控制进程或缩小池大小，而不是继续扩大单池密度。

## 五、百万用户Cloud Agent：具体落地实验

建议用**一条Sandbox生命周期控制面链路**先做可复现试验：

1. **Identity与Policy Gate：** 所有创建、执行、网络出口、挂载、恢复操作携带tenant_id/principal_id/task_id/policy_version；网关默认拒绝匿名，敏感动作在执行前重新鉴权。记录allow/deny、凭据来源、审计关联ID。
2. **Task状态机：** 将CREATED→RUNNING→SUSPENDING→SUSPENDED→RESUMING→RUNNING/FAILED/NEEDS_REVIEW明确化；区分“计算状态恢复”“工作区文件恢复”“模型上下文恢复”和“业务副作用恢复”。任务checkpoint与用户持久Workspace放在独立持久层，Sandbox仅是可替换执行容器。
3. **Budget Broker：** 对每个租户/会话预留token、推理调用、沙盒CPU秒、存储与工具费用预算；并发任务使用原子配额预留、完成对账与超额熔断。SDK预算只是用户界面，不是唯一强制点。
4. **Supervisor混沌实验：** 在相同硬件与任务混合负载下比较per-sandbox与shared-pool模式，测量P95恢复耗时、冷启动、控制面CPU/RAM、每沙盒常驻开销、故障影响面、交互重连成功率；注入Supervisor进程退出、网络分区、旧版组件混用、恢复失败、重复请求和凭据撤销。按租户SLO决定是否启用实验性池化。
5. **幂等与撤销：** 文件写入、消息发送、支付等工具必须有独立idempotency_key与审计Outbox；恢复和fork前重新检查授权、预算与任务版本；取消请求需要向远端MCP/工具传播，并验证无孤儿副作用。

优先级建议：P0做默认拒绝、审计、撤销与恢复状态机；P1做预算Broker和驱动兼容矩阵；实验性共享Supervisor先灰度压测，**不直接用于生产默认路径**。

## 数据质量与交付边界

本次读取时，仓库的intel/daily/2026-10-29.json尚不存在；最近triage及quality均为10月28日采集。该快照显示19个信源中18个抓取成功、deepmind-blog失败；55条候选、186条跨日未核验积压；这些数字反映采集健康与待审队列，**不代表重要事件召回率**。coverage当日可评估gold样本为0，不能计算召回率。intel/events.json目前只有2条旧的人工核验事件；新的官方Release已独立阅读，但未擅自写入其编辑审核账本。

长期预测仍有2条开放、0条到期、0条判定；不改动冻结概率。今日不做长期KG实体/Monograph/Asset变更，Delta仅包含四组空数组；没有以发布说明冒充完整schema级知识审查。

## Sources

1. NVIDIA OpenShell，v0.1.6正式Release，UTC 2026-10-27 17:56:58：https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.6
2. OpenHands software-agent-sdk，v1.59.0正式Release，UTC 2026-10-28 14:34:44：https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.59.0
3. OpenAI Codex，v0.165.0正式Release，UTC 2026-10-27 20:09:38：https://github.com/openai/codex/releases/tag/rust-v0.165.0
4. OpenAI，Introducing the Agents API，2026-09-10，public beta：https://openai.com/index/introducing-the-agents-api/
5. AWS，AgentOps: Operationalize agentic AI at scale with Amazon Bedrock AgentCore，2026-06-01：https://aws.amazon.com/blogs/machine-learning/agentops-operationalize-agentic-ai-at-scale-with-amazon-bedrock-agentcore/
6. Anthropic，AI for Science expands to foundations and research institutions，2026-10-28：https://www.anthropic.com/news/ai-for-science-expands-foundations-research-institutions
7. Anthropic，Previewing the Model Hardware Standard，2026-08-27：https://www.anthropic.com/news/model-hardware-standard-research-preview
8. LangGraph，官方Releases，近期v1.2.18及Checkpoint v4.3.1（10月27日北京，作为恢复语义对照）：https://github.com/langchain-ai/langgraph/releases
