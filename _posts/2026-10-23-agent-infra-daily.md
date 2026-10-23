---
layout: post
title: "Agent Infra Daily · 2026-10-23｜决策执行分层与跨云 Agent 治理"
date: 2026-10-23 08:30:00 +0800
summary: "OpenAI Decisions API 转为 GA、Claude Platform 的 Anthropic-managed Google Cloud 方案 GA、Uber 大规模推广 ChatGPT Work：关注 Agent 高频决策成本、跨云身份和企业连接器治理。"
tags: [agent-infra, strategic-analysis, cloud-agent, decisions-api, model-routing, enterprise-agents, identity-governance]
---

> **补刊说明（北京时间 2026-10-23）**：原每日任务已触发，但截至当日约 16:04 未把日报及知识增量提交到 \`main\`。本篇为当日补刊，不伪装成 08:30 已发布的报告。研究以 **2026-10-22—2026-10-23** 已能核验的一手资料为基础；部分公告只标“10 月 22 日”，**没有可核实的精确发布时分/时区**，故不能断言其全部严格位于北京时间 08:30 截止的 24 小时窗口。本文是行业分析，不是项目 PR 清单。

## 今日核心判断

**Agent Infrastructure 正在出现两层明确分工：高频、低延迟的结构化决策逐渐从长文本推理调用中独立出来；模型、计费与身份入口则开始出现“同一云入口、不同模型厂商负责数据处理”的双重治理路线。** 同时，企业多应用 Agent 推广进入数万员工的**覆盖部署阶段**。这些信号意味着百万用户 Cloud Agent 需要分别优化决策路径、授权路径和长任务执行路径，而非全部包进一个 LLM Loop。

## 关键行业与生态进展

### 1. 高频 Agent 决策成为独立的 API/成本层（P0）

**2026-10-22**，OpenAI [正式宣布 Decisions API GA](https://openai.com/index/decisions-api/)。[开发文档](https://developers.openai.com/api/docs/guides/decisions)说明 \`POST /v1/decisions\` 使用 \`gpt-6-luna\`，提供布尔判断、限定候选选择与评分，可从文本、图像、JSON 及工具调用上下文得到**有界结构化结果**；单请求最多 400 个问题，支持提示缓存。官方表示与同模型 Responses API 路径相比，指定条件下可快至约 10 倍；定价参考为非缓存输入每百万 token **0.10 美元**，仅按输入计费，仍需注意区域与缓存定价条件。

**架构级意义**：判断是否需要检索、路由哪个工具、风险等级、是否触发人工审核，通常不需要完整的生成式回答。引入 **Decision Plane → Planning/Generation Plane → Execution Plane** 的分层，可将频繁的小决策与长上下文推理分别计量、灰度、评测和缓存。

**证据边界**：速度数字来自厂商及特定客户样本，不是跨负载通用 SLA；其输出概率也不等于经过校准的安全许可。对于付款、删除、执行 Shell 等高风险动作，必须有确定性策略与显式授权门禁；Decision API 只能提供辅助信号。

### 2. 跨云模型接入进一步分裂身份、计费和数据处理责任（P0）

**2026-10-22**，Anthropic 宣布 [Claude Models on Google Cloud（Anthropic managed）正式 GA](https://claude.com/resources/articles/claude-models-on-google-cloud-anthropic-managed)。客户可用 Google Cloud IAM 身份与统一账单接入原生 Claude Platform 能力，由 **Anthropic 作为数据处理方**；另一条 **Google managed** 路线则以 Google 作为数据处理方，更适合某些数据驻留和 Google 原生安全集成场景。

文档列举 Managed Agents、代码执行、Computer Use、Skills、MCP Connector 等能力，但**Anthropic-managed 接入 GA ≠ Managed Agents 或 MCP Connector 全部 GA**；原文分别将后两者标为 **beta**。目前 Anthropic-managed 的端点为 US 与 Global，也不能推断具备任何地域驻留诉求下的等价选择。

**架构级意义**：Model Gateway 的一行 model/provider 路由字段远远不够。至少还要记录 \`processor\`、\`identity_provider\`、\`billing_boundary\`、\`data_region\`、\`feature_maturity\`、\`allowed_tools\` 和 \`retention_policy\`，并将任务、Workspace 和 Credential 的保留周期独立建模。模型访问渠道可迁移，不等于 Agent 运行状态可迁移。

### 3. 企业 Agent 进入大范围授权部署阶段（P1）

OpenAI [10 月 22 日公告](https://openai.com/index/uber-chatgpt-work-rollout/)称 Uber 将 ChatGPT Work 从 **1000 人试点**扩展为面向 **3 万余名员工**的企业级推广，并配套内部 Skills 库、批准的集成和培训。涉及 Google Drive、Gmail、Calendar、Slack 等企业应用。

**架构级意义**：在生产部署中，真正稀缺的不只是模型推理，还包括 IT 集成审批、员工权限继承、数据访问审计、Skills 生命周期和变更治理。平台应能以企业/租户/用户/任务四层边界管控远程连接器，并测量成功任务成本和人工接管率。

**证据边界**：公告核实的是**宣布推广与计划覆盖人数**，不等于已有 3 万名活跃使用者，更不等于独立验证了任务成功率、节省工时或生产事故率；公告也说进一步的采用与成效数据尚待披露。

## 技术路线与竞争格局

| 战略层 | 典型路线 | 收敛方向 | 仍然存在的分歧/代价 |
|---|---|---|---|
| 高频决策层 | 专门的 Decision API / 小模型 / 确定性规则 | 有界判定与生成式推理解耦，独立评测成本和延迟 | 模型信号不能直接取代强制授权；误判与校准成本 |
| 模型访问控制层 | 厂商原生 API / 云代理的 Anthropic-managed / Google-managed | 模型能力与企业 IAM、结算逐步解耦 | 数据处理方、地理驻留、功能同步、预览成熟度不等价 |
| 企业 Agent 平台 | 托管 Work + 受控连接器 / 自建 Runtime | Skills、工具审计、身份与业务工作流进入平台级治理 | 供应商锁定、跨应用失败补偿、真实 TCO 和生产指标仍有限 |
| 可恢复执行层 | Durable Task / Event History / 持久 Workspace + Sandbox | 控制状态、文件状态、权限状态应明确区分 | 尚无证据表明上述三项新公告解决了端到端可恢复语义 |

与 **10 月 21 日背景基线**（Claude Duet research preview、Google Cloud OpenAI 模型 private preview）相比，今天的新增证据更偏向 **API 功能正式成熟度和企业交付控制面**，不应错误归类为跨厂商 Agent State Portability 已解决。

## 研究与标准

本轮已核验的实质性正式更新为 **Decisions API GA** 和 **Claude Platform Anthropic-managed Google Cloud 接入 GA**。没有在本次核验中确认新的 MCP/A2A 正式跨厂商状态迁移标准或可独立复现的 Agent 长任务恢复 benchmark。

值得追踪的是 OpenAI [Decisions 开发文档](https://developers.openai.com/api/docs/guides/decisions)明确指出：有界判断适合专门 API，生成自定义结构需要 Structured Outputs，调用工具仍需外部 Function Calling 和策略执行。不能因为“判定 API 返回信心分数”就放弃高风险工具的最终授权和失败补偿。

## 7 日 / 30 日趋势雷达

| 长期命题 | 当前判断 | 本日证据和待证伪点 |
|---|---|---|
| Agent 控制面分层 | **加强** | Decisions API GA；需验证其在真实长任务路由中的净收益 |
| 跨云模型/身份治理 | **加强** | Anthropic-managed 在 Google Cloud GA；处理方与地域差异仍在 |
| 企业 Agent 生产化 | **加强但需观测** | Uber 扩大推广覆盖；实际活跃率、任务成功率尚未公开 |
| Always-on / Durable Runtime | **待证实** | 此轮无独立可复现恢复 SLA，Duet 仍属此前研究预览背景 |
| 跨厂商 Task/Workspace/Authority 可移植 | **待证实** | 多模型接入不等于 Checkpoint 或权限链可迁移 |
| Agent RSI 的可验证长期改进 | **待证实** | 无新的公开独立纵向对照证据 |

标签为研究判断，不是经过统计校准的概率。两项已预登记长期预测（工具会话策略、托管 Workspace 跨版本保留）**本日均未到期，不更改主观概率或未来判定条件**。

## 百万用户 Cloud Agent 工程启示

**P0 — 先建设轻量 Decision Plane 的 A/B 能力。** 对 ToolRouter、触发筛选、任务优先级及风险初筛设独立接口，严格拆分确定性规则与模型估计。用相同任务集比较成本/每次判定、端到端任务成功率、p95 路由耗时、误拒和高风险误放行；不要直接搬用厂商“10x”。

**P0 — 建立模型接入的治理元数据与不变量。** 将云接入商与实际模型数据处理方分开，明确数据地域、工具白名单、计费路径、权限与功能成熟度。一个租户允许某模型，不等于允许所有地区、beta 工具或数据处理路线。

**P1 — 以企业集成生命周期做压力测试。** 从 1000 → 30000 用户的真实难点在 Token 授权/撤销、连接器配额、状态恢复和企业审计。先模拟 Connector 撤销、审批超时、重试重复执行、组织权限变更，度量跨租户误读率、撤销生效时间、恢复成功率和单位成功任务 TCO。

**P1 — 守住三个持久状态域。** Task Journal、Workspace Snapshot 和授权/审计记录分别持久化，生命周期不要统一绑定 Worker 或模型 Session。保持模型与执行后端可替换，避免因为跨云模型 GA 而做无依据的大规模迁移。

## Sources（官方，均标示 2026-10-22；具体公开时刻不全部可核验）

1. [OpenAI — Decisions API GA](https://openai.com/index/decisions-api/)；[开发者 API 指南与边界](https://developers.openai.com/api/docs/guides/decisions)；[开发者更新记录](https://developers.openai.com/api/docs/changelog)。
2. [Anthropic — The full Claude Platform, available on Google Cloud](https://claude.com/resources/articles/claude-models-on-google-cloud-anthropic-managed)。
3. [OpenAI — Uber brings ChatGPT Work to all employees](https://openai.com/index/uber-chatgpt-work-rollout/)。
4. 历史基线（非今天新发布）：[Anthropic — Claude Duet](https://claude.com/resources/articles/claude-duet)；[Google Cloud — OpenAI models in Model Garden](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-brings-openai-models-to-customers)。
