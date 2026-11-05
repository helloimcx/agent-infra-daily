---
layout: post
title: "Agent Infra Daily｜2026-11-05：共享Sandbox控制面需要故障与审计契约"
date: 2026-11-05 08:00:00 +0800
summary: "OpenShell v0.1.7稳定版将OCSF审计统一至1.8.0，完善共享Supervisor故障恢复、Kubernetes沙盒更新和OTLP链路；Codex 0.168.0-alpha.2仍属预发布。百万用户Cloud Agent应将控制面HA、审计兼容性和业务幂等分开验证。"
tags: [agent-infra, sandbox, runtime, observability, security, cloud-agent]
---

## 今日核心判断

**Sandbox从单实例隔离走向共享监督控制面时，成本与高可用的权衡必须通过故障边界、审计格式及执行幂等契约共同验证。** 本次独立核验未发现过去约24小时内足以认定为跨行业P0的正式标准或生产规模突破；重点回看北京时间11月4日凌晨发布的OpenShell稳定版，并核对北京时间11月5日凌晨Codex预发布。正式版本不等于所有实验功能已达生产成熟度。

## 一、OpenShell v0.1.7：控制面可靠性与审计兼容性

**已核实事实。** NVIDIA/OpenShell v0.1.7官方Release于2026-11-03 19:24 UTC（北京时间11月4日03:24）发布，标记非Pre-release。升级后仅输出原生**OCSF 1.8.0**审计事件，旧1.1/1.3格式不再输出，旧版本配置被弃用；共享Supervisor超过60秒恢复期限的Sandbox会转为Stopped，支持显式重新启动；共享池放置失败会给出更具体原因。Kubernetes Sandbox支持停止后更新镜像、命令、环境及元数据，保留持久卷，但需operator启用；Agent可通过网关转发OTLP traces，网关附加Sandbox ID，支持HTTP、认证头和私有CA/mTLS等配置。

**证据边界。** 共享Supervisor属于**实验性**，官方明确故障接管可能短暂冻结任务、交互连接需重连，超时仍会终止工作负载。版本说明不是独立的p99、故障恢复SLA或百万租户容量证明。OCSF版本变更属于破坏性兼容性升级，需要验证下游SIEM解析、告警和保留策略。官方：https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.7

**架构Tradeoff。** 共享监督降低每Sandbox的控制进程开销，却增加故障相关性和容量热点；单Sandbox监督隔离更直观，但资源成本更高。选择应依据故障注入下的恢复时间、影响租户数、网络连接恢复率与单位活跃任务成本，而非仅比较内存占用。

## 二、Codex 0.168.0-alpha.2：预发布不能当生产承诺

**已核实事实。** openai/codex官方Release API显示0.168.0-alpha.2于2026-11-04 20:47 UTC（北京时间11月5日04:47）发布，标记**Pre-release**。本次不据此推断稳定版已有新的执行恢复、审批或权限能力；应等待稳定版Release Notes与可重复测试。官方：https://github.com/openai/codex/releases/tag/rust-v0.168.0-alpha.2

## 三、跨厂商路线与标准/研究

OpenShell强调隔离执行、监督进程和审计；AWS AgentCore强调托管Runtime与会话入口；Google Agent Executor公开强调事件日志与快照恢复。它们分别提供**沙盒隔离、托管运行、任务恢复**的不同构件，不可互相替代。已有MCP/A2A协议能力不能证明跨租户的授权撤销、幂等执行或审计链路已完整实现。本次未核实新MCP/A2A正式标准发布，也未发现足以改写长期选型的独立Benchmark。

参考：https://cloud.google.com/blog/products/ai-machine-learning/agent-executor-googles-distributed-agent-runtime/ ；https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ ；https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.7

## 四、7/30天趋势雷达（分析判断）

| 时间窗 | 判断 | 支持与反证边界 |
| --- | --- | --- |
| 7天 | **加强**：Sandbox共享控制面与审计格式产品化 | OpenShell稳定版修复恢复与审计问题；共享Supervisor仍实验性 |
| 7天 | **待证实**：Codex预发布对持久执行的影响 | Alpha缺少足够稳定能力证据，不能作为GA |
| 30天 | **加强（低置信）**：身份、工具治理、任务状态独立控制面 | 多厂商架构材料共现，但缺少可比的生产SLA |
| 30天 | **待证实**：共享Supervisor净成本收益 | 缺少公开跨租户故障相关性、p99和规模Benchmark |
| 30天 | **未发现足以推翻的证据**：长期趋势假设 | 缺少证据不代表预测成立；不改变既有注册概率 |

## 五、百万用户Cloud Agent工程建议

1. 建立**Sandbox Supervisor Contract**：明确sandbox_id、supervisor_epoch、租户隔离域、lease、故障期限与重连令牌；重连必须重新校验权限和预算。
2. 为共享池开展**故障注入**：杀死Supervisor、切断Gateway、让恢复超过60秒，测冻结时长、影响Sandbox比例、连接恢复成功率和残留任务。
3. 建立**审计兼容性门禁**：在OCSF 1.8.0迁移前验证字段映射、拒绝事件、凭证异常告警与OTLP链路完整性；审计采集失败不能默默降级为“成功执行”。
4. 将Sandbox进程恢复与**业务Execution Ledger**分离：文件写入、发送消息、支付等副作用必须有幂等键、外部回执与unknown状态；Supervisor恢复不自动意味着可重试业务操作。
5. 对独立Supervisor与共享池做同负载A/B：比较p95/p99恢复、隔离失效半径、CPU/内存、审计完整率和单位成功任务成本，不引用厂商性能结论代替实测。

## 六、数据质量与KG处理

北京时间11月5日08:02读取时，`intel/daily/2026-11-05.json`尚不存在。最近可读的11月4日质量快照为19/19信源抓取成功、56条当期候选、339条跨日未核验积压；triage队列28条，仍为未验证候选。编辑确认事件库仅2条，独立Gold评估符合条件样本为0，不能计算有效召回率。两条预测均到2027-03-31才到期，原条件、概率及判定状态保持不变。

本次仅记录日报分析，不改动长期KG Entity/Pattern/Trend，Delta四组空数组。信源抓取成功不代表覆盖所有重大进展。

## 官方Sources

- https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.7 （2026-11-04北京时间，稳定版）
- https://github.com/openai/codex/releases/tag/rust-v0.168.0-alpha.2 （2026-11-05北京时间，Pre-release）
- https://cloud.google.com/blog/products/ai-machine-learning/agent-executor-googles-distributed-agent-runtime/ （历史架构对照）
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ （历史架构对照）
