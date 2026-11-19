---
layout: post
title: "Agent Infra Daily｜2026-11-20：成本治理与 Sandbox 权限边界"
date: 2026-11-20 08:00:00 +0800
summary: "Airbnb 生产实践强调单位任务成本与上线后观测的差异；Codex Sandbox 技术解析揭示本机执行、MCP 子进程和网络代理的安全边界。"
tags: [agent-infrastructure, cloud-agent, sandbox, evals, observability]
---

## 今日核心判断

**生产级 Agent 的两个关键控制面是经济性与执行权限：离线评测决定模型候选，生产观测持续纠偏；Sandbox 限制命令，但不能替代工具身份、授权和副作用审计。** 本次独立核验了两篇11月18日正式发表的一手技术文章（均非11月20日新版本）；过去约24小时有限检索未确认新的 P0 正式标准或重大架构发布，不将旧闻包装成今日新品。

## 重大进展与证据边界

### 1. Airbnb / AWS：从 token 单价转向 Cost per Task（P1 生产实践）

AWS 2026-11-18 官方联合文章披露：Airbnb 内部 AirChat 和 AirChat Remote 经由自建 LLM Gateway 调用 Bedrock。团队使用真实工程任务、可重复 grader 和不同 reasoning effort 评估模型，以完成一项任务所消耗的全部请求 token 的标价成本定义 cost per task；上线后结合 CloudWatch、网关归因和实际使用强度重新评估默认模型。文章披露一个匿名模型从低到高推理档位，评测分数仅增加0.8而任务成本变为2.5倍；另一次迁移后，重度用户群在首个完整周对主要模型的花费约降至原先七分之一。**这些是企业自述案例，不是可推广到所有任务的性能基准。** 文章还指出 quota 预留与实际账单不同，cache read 不计入其所述请求预留却仍有计费，max_tokens 会影响准入；生产用户行为可能令离线最优选择失效。

### 2. OpenAI：Codex Sandbox 公开机制与边界（P1 架构解析）

OpenAI 2026-11-18 工程文章解释，Codex 倾向使用操作系统原生沙盒而非强制将本地工作环境复制到容器；以 permission profile 约束文件与网络，命令执行经 harness 判断权限，有限网络访问通过代理执行。默认 workspace profile 允许工作区写入但保护部分配置目录、允许较广泛的文件读取并关闭网络。**关键反证：广泛读取仍可能接触敏感配置，恶意修改被 Git 忽略的依赖可能产生后续执行风险；stdio MCP Server 默认启动命令并不自动套用 shell sandbox。** 官方给出使用 `codex sandbox` 显式包裹 MCP Server 的示例。文档描述设计与能力，不等于多租户云环境安全证明。

## 主流架构与 Tradeoff

- **本机原生 Sandbox（Codex）**：保留开发者真实工具链，环境兼容性高；宿主机读权限、未受控子进程和隐蔽副作用需要补偿控制。
- **隔离 Cloud Workspace / Sandbox**：更易控制租户边界、生命周期和配额；付出启动、镜像分发、持久存储和恢复迁移成本。
- **多模型 Gateway + 任务级 Evals（Airbnb）**：模型路由可按质量/成本快速调整；需要持续维护任务集、grader、归因与线上漂移监控。

## 标准与研究

本次未确认新的 P0 正式标准发布。MCP 连接性不自动等于授权传播或工具执行安全；推理 effort 与成本的权衡应在本企业任务集上复测，不能直接套用厂商 benchmark。

## 7 / 30 天趋势雷达

- **加强（7天）**：模型选择与运行时治理从单次请求指标转向任务完成质量、成本、权限及恢复边界；近期 Airbnb 实践和 Codex 机制披露提供两条独立证据，但不是采用率统计。
- **待证实（30天）**：跨 Provider 统一的执行授权、Sandbox 迁移和恢复契约，缺少独立多租户故障注入与规模化成本基准。
- **减弱/推翻**：没有足够可复验证据判定；不强行改变长期趋势状态。

## 百万用户 Cloud Agent：具体工程建议

1. **建立 Task Economics Ledger**：以 tenant/task/run/model/effort 关联 token（区分 uncached/cache read/cache write/output）、工具耗时、Sandbox 秒数、重试和成功判分；同时展示 cost per successful task 与 p95/p99 完成时延，避免仅优化每百万 token 价格。
2. **建立 Model Admission Controller**：离线固定任务集测质量、成本、延迟；线上按成功率、用户使用强度、quota reservation 与 throttling 纠偏。模型切换要验证备用模型的质量和实际容量。
3. **建立 Sandbox Permission Fence**：工具进程与 MCP Server 同样经过显式隔离；对敏感路径采用 deny、网络出口代理和每次调用身份校验；外部写入使用幂等键与执行账本，恢复前核对未决副作用。
4. **故障注入**：覆盖缓存命中率下降、max_tokens 准入变化、MCP 子进程越权、权限撤销、Sandbox 重建和工具回执丢失。禁止将隔离机制本身当成 Exactly-once 保证。

## 情报质量与预测

截至本次读取，2026-11-20 的采集快照不存在；最近可用 11-19 快照为 18/19 信源健康，失败源 `deepmind-blog`，当期93条候选、跨日未核验796条。独立 Gold 样本为0，重要事件召回率不可计算；采集成功不等于覆盖完整。已登记两项 2027-03-31 预测均未到期，不更改条件、概率或结果。

## 官方 Sources

- AWS / Airbnb, 2026-11-18, [How Airbnb uses cost per task to operate coding agents on Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/how-airbnb-uses-cost-per-task-to-operate-coding-agents-on-amazon-bedrock/)
- OpenAI, 2026-11-18, [Inside the Codex sandbox](https://openai.com/index/inside-the-codex-sandbox/)
