---
layout: post
title: "Agent Infra Daily｜2026-10-28：A2UI推理格式解耦与可验证多Agent执行"
date: 2026-10-28 08:00:00 +0800
summary: "Google于10月27日发布A2UI可切换推理格式方案，提出模型生成中间DSL、确定性编译为受控组件消息；另以多Agent电商原型分析异步入口、状态分层、确定性副作用与生产证据边界。"
tags: [agent-infra, cloud-agent, harness, a2ui, generative-ui, runtime, evaluation, multi-agent]
---

## 今日核心判断

**Agent界面与执行架构正在同时走向“生成意图与确定性契约分离”。** 对于交互层，模型不必直接生成冗长、易错的完整UI JSON；可以生成更紧凑的中间表达，再由受控编译器转换为客户端已授权的组件协议。对于执行层，入口事件、可恢复业务状态、模型决策与具有副作用的工具应各自遵守独立契约。两个方向都指向同一工程原则：**让模型负责不确定性，让代码负责边界、状态和可验证性。**

截至北京时间2026年10月28日08:00，独立打开了Google开发者官方两篇标注10月27日的技术文章。官方页面仅给出发布日期，未给出精确时区与小时，因此只能确认它们属于**10月27日官方公开内容**，不能断言均严格落在北京时间过去24小时。尚未看到足以证明跨厂商广泛生产采用或百万用户规模性能的独立数据；不把原型、厂商测试或宣称的倍数视为通用SLA。

## 一、重点进展与证据边界

### 1. Google A2UI引入可切换 inference format：传输协议与模型生成语法解耦

**已核验事实｜Google Developers Blog，2026-10-27。** A2UI的客户端先声明可信组件Catalog；Agent生成UI描述，客户端使用允许的组件渲染。新方案让模型生成A2UI Express等中间格式，由Agent SDK中的确定性编译器转为经过Catalog校验的标准A2UI消息；生成提示与编译器均从Catalog schema导出。Python SDK已提供ExpressFormatFactory，TypeScript与Dart SDK亦有对应实现，版本与成熟度并不完全相同。官方将Express称为新默认推理格式，而不是新建一个不兼容的UI传输协议。

**量化边界：** 官方称Express相比直接生成JSON可减少至多约3倍token、改善至多约3倍延迟；并展示使用Jev决策模型选择预定义布局的原型，宣称某些场景至多约80倍提速。Express的比较来自同一团队在51个任务上的实验；Jev演示仅11个prompt，组件树约92–298ms出现、完整页面约0.8–1.7秒，官方明确指出样本小。**这些数字不是跨模型、跨设备或生产P95的保证**。

**重要tradeoff：** Direct JSON可逐块流式编译；当前Express需要等模型完整回复后再编译。预定义布局的决策模型更快，却无法表达语法未涵盖的新布局；Express保留更高表达力，代价是更长生成链路。正确选型应比较端到端首屏时间、完成时间、token、无效结构率、组件安全违规率、终端可访问性与缓存命中，而不是只比模型首token延迟。

**百万用户工程建议：** 将UI Contract设计为 `catalog_version + component_allowlist + action_schema + renderer_capabilities`，中间格式作为可替换编译插件；所有Event在服务端按用户/租户/任务授权，绝不因为组件来自可信Catalog就自动授予后端写权限。设置Direct JSON、Express和模板决策三路灰度，统一记录解析失败、编译耗时、首屏P95、动作误触发及回滚率。

### 2. Google多Agent电商原型：异步入口、会话状态和确定性交易工具的三层拆分

**已核验事实｜Google Developers Blog，2026-10-27。** HappyDelivery技术文章明确自称**working prototype**，采用Ingress（Webhook签名验证、标准化、快速入队）、Session/Cart（Redis存放活跃购物状态）、Agent Swarm（LangGraph/Gemini与专用工具）三层。消息入口先验证不同渠道签名并归一化为事件，快速确认后再由异步工作流处理；会话层保存购物车与偏好；支付使用tokenized引用而非将原始卡号输入模型。作者还描述状态机、确定性交易工具与自动验证套件。

**关键限制：** 原文给出Redis QPS、百万购物车容量等估算，并讨论消息确认时间，但文章是架构示例，**并非经过独立审计的百万并发真实负载报告**。Redis能承载会话缓存不等于全链路能承载同等TPS：模型推理、下游支付、租户隔离、队列积压、重试风暴、幂等和成本均可能先成为瓶颈。原型的“pause/resume”主要体现状态恢复，不自动证明工作流具备exactly-once副作用或灾难恢复保证。

**百万用户工程建议：** 为入口事件生成稳定的 `event_id` 和 `tenant_id`，用Inbox去重；对支付/写文件/发送邮件等动作采用 `idempotency_key`、Outbox及人工审批边界；将Redis定位为热状态，将可审计事件日志和任务checkpoint落在持久存储；对超时重试、重复Webhook、跨租户读取和任务恢复做故障注入。

### 3. 标准生态背景：Skills中立治理与A2UI组件契约分属不同层

**历史对照，不是今日新发布。** Anthropic在2026-10-22宣布将Agent Skills标准移交Agentic AI Foundation。Skills主要定义Agent可加载的任务知识与工作流打包方式；A2UI定义受控组件驱动的交互消息。两者并非替代关系：前者回答“Agent怎样学会完成任务”，后者回答“Agent如何在安全组件边界内呈现和收集交互”。目前没有足够一手证据证明两套规范在所有Agent框架中已经端到端互操作。

## 二、主流路线与架构取舍

**Google A2UI路线：** 可信组件Catalog + 可替换生成语法 + 确定性编译 + 客户端Renderer；适合表单、任务审批、云电脑辅助面板等需要交互但不能让模型执行任意前端代码的场景。代价是Catalog版本兼容、编译器维护、服务端Event鉴权与客户端状态同步。

**传统结构化输出路线：** 模型直接生成JSON Schema约束的UI AST，组件少时实现简单、流式能力直观；复杂树结构可能增加token和格式错误。**模板/决策模型路线：** 对固定页面的布局分类、组件选择更快，但遇到开放式内容、未知组件关系时表达能力不足。建议用任务复杂度和可预定义程度路由，而非押注单一格式。

**多Agent路线：** Supervisor + Specialist可将权限与上下文按职责收窄；但多跳推理增加成本、延迟和失败传播面。只有当任务的工具边界、责任划分或评测收益可量化时才值得拆分；否则优先单Agent + 显式工具契约。

## 三、标准、研究与证据质量

A2UI新格式说明的是**SDK与推理格式层的实现能力**，不代表所有客户端均已支持，也不代表标准制定组织已经给出通用互操作认证。Google的51任务内部对比与11任务原型是有用的方向性证据，但缺少独立重现实验、真实移动端冷启动分布与安全评估。10月22日Skills治理变动是组织层事实，尚不足以推断实际迁移成本或安全收益。

研究系统方面，仓库最近的 `intel/events.json` 仅有2条经过人工一手核验的旧事件，不能把新的RSS候选自动晋升为“verified”；`intel/trends.json` 的工具治理方向仍是低置信度加强，其余长期假设多为未评估。长期预测2条均未到2027-03-31截止日，不进行YES/NO判定，也不改变冻结概率。

## 四、7天／30天趋势雷达

**7天｜加强（方向性）：** 受控工具与UI契约、Agent评测与可审计执行的官方工程实践出现多点证据。A2UI在生成层加入确定性编译，是一条新的技术实现证据；不能直接外推为行业普遍采用。

**7天｜待证实：** 决策模型生成UI在复杂动态页面、弱网移动端与混合组件版本下的端到端优势；多Agent电商原型在真实支付重试与租户隔离下的可靠性。

**30天｜加强但置信度有限：** 工具发现/调用授权分层、长任务状态独立于模型上下文、结构化可观测与评测契约逐渐成为架构关注点。该结论是跨来源定性归纳，不是采用率统计。

**30天｜尚无足够证据推翻：** 当前没有足够一手证据推翻可替换Sandbox、分层记忆或可验证Agent改进的研究假设；“没有证据推翻”不等于已经证明。若真实场景发现中间格式编译显著增加首屏P95，或模板覆盖率不足，应下调相关路线优先级。

## 五、百万用户Cloud Agent：下一步可执行设计

建议优先实施一个小型 **Agent UI Contract Gateway** 实验：把 `task_id/tenant_id/principal_id/catalog_version/action_id` 贯穿生成、编译、渲染、用户确认与工具调用；所有动作需服务端重新鉴权并记录 `policy_decision`。选择“文件搜索结果卡片”“云电脑操作确认”“长任务进度/恢复”三种真实场景，在相同模型与输入下A/B比较Direct JSON、Express和预定义模板，采集P50/P95首屏、总耗时、token成本、UI错误、动作安全失败、断线重连一致性；对高风险操作强制人工确认。实验前冻结任务集和通过标准，避免事后挑选样本。

执行面继续沿用 `Ingress → durable event log → task checkpoint → policy-gated tools → audited side effects`。UI的“点击批准”只是一个带身份的事件，不是无条件执行权限；恢复后必须重新检查授权有效期、任务版本和幂等键。优先把这些约束写入接口与回归测试，而不是先增加Agent角色数量。

## 数据缺口与交付边界

北京时间08:00读取时 `intel/daily/2026-10-28.json` **尚不存在**；最近 `intel/triage/latest.json` 与质量快照仍是10月27日数据。最近快照显示19/19信源抓取成功、40条候选、170条跨日未核验积压；这些指标仅代表抓取健康与候选数量，**不代表重要事件召回率**。coverage样本当日eligible为0，不能计算行业召回率。独立一手检索补充了Google 10月27日的两篇文章，但并非对全部厂商与论文库的穷尽审计。

没有进行经过schema与完整Monograph/Asset门槛的长期KG实体改动；今日Delta保留四组空数组。未来若有可复验的生产证据，再审慎晋升节点与趋势，不以新闻标题代替验证。

## Sources

1. Google Developers Blog，2026-10-27，**Fast, reliable A2UI, with swappable inference formats**：https://developers.googleblog.com/fast-reliable-a2ui/
2. Google Developers Blog，2026-10-27，**Building Conversational Commerce with Multi-Agent Swarms on GCP: A Working Prototype**：https://developers.googleblog.com/building-conversational-commerce-with-multi-agent-swarms-on-gcp-a-working-prototype/
3. Anthropic，2026-10-22，**Donating Agent Skills to the Agentic AI Foundation**：https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation
4. Google Developers Blog，2026-10-15，**Evaluating AI agents: moving past the vibe check**：https://developers.googleblog.com/evaluating-ai-agents-moving-past-the-vibe-check/
