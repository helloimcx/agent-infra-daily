---
layout: post
title: "Agent Infra Daily｜2026-11-16：从可恢复执行走向可审计的副作用控制"
date: 2026-11-16 08:00:00 +0800
summary: "过去约24小时未确认新的P0级正式架构或标准发布；对比LangGraph、OpenShell与Codex近期一手资料，提出百万用户Cloud Agent的恢复、授权和执行账本设计。"
tags: [agent-infrastructure, cloud-agent, durable-execution, sandbox, security]
---

## 今日核心判断

**可恢复的 Agent 不是可重复执行的 Agent。** 对百万用户 Cloud Agent，模型会话、工作区、任务检查点、权限和外部副作用必须采用不同的持久化与失效契约。过去约24小时（北京时间11月15日08:00至11月16日08:00）有限独立检索未确认新的P0级正式架构、标准或生产能力发布；不能把旧公告或网站 lastmod 当作今日事件。

## 重大进展与证据边界

1. **LangGraph 的恢复语义仍值得作为对照。** 11月5日正式版1.2.20为任务内每次 interrupt 分配ID，并引入拒绝过期回答的 strict resume；11月6日SDK 0.4.14提供相应调用接口。它解决恢复状态一致性的一部分，不保证第三方API的Exactly-once，也不是今日新品。官方：https://github.com/langchain-ai/langgraph/releases
2. **LangGraph.js 取消传播补齐运行生命周期。** 11月9日23:58 UTC发布的1.7.3修复退出流迭代后后台节点继续运行的问题。取消流消费不等于撤销已送达的外部写操作。官方：https://github.com/langchain-ai/langgraphjs/releases
3. **OpenShell 的生产路线强调隔离与运维门禁。** 官方0.1.0里程碑列出稳定版本资格测试、升级和API兼容政策，但实验性功能仍须逐项验证；不能据此推导百万租户规模的故障域和成本。官方：https://github.com/NVIDIA/OpenShell/milestone/10

## 厂商与架构路线：Tradeoff

LangGraph侧重有状态编排和人机中断恢复，适合显式任务图；代价是Checkpoint版本、状态归约和工具副作用仍需业务实现。OpenShell侧重Sandbox隔离、执行边界及审计，代价是控制面与工作区持久性、租户资源配额需另行设计。Codex代表多会话工作台与Provider适配路线，但UI会话恢复不等于执行后端迁移。三条路线互补，尚无充分证据证明通用的跨供应商Durable Runtime标准已成熟。

## 标准与研究

工具发现协议不等于持续授权或跨调用的时序策略。对于MCP/A2A等协议，必须分开核验发现、认证主体传播、撤权、审计和重试语义。近期没有足够一手证据支持新标准正式落地的判断；不推断采用率或性能Benchmark。

## 7/30天趋势雷达

- **加强（7天，工程方向判断）**：恢复一致性、取消传播和Sandbox最小权限逐步成为独立治理问题；证据来自近期多个项目的发布说明，不代表行业部署占比。
- **待证实（30天）**：多后端Agent工作台能否跨Provider迁移Checkpoint和Workspace；需要端到端迁移测试。
- **待证实（30天）**：共享Supervisor在故障与租户隔离下的净成本收益；需要p99延迟、故障半径和内存曲线。
- **未观察到可判定减弱或推翻的趋势**；历史假设不能因日报缺席自动改写。

## 百万用户Cloud Agent：本周工程建议

实现五个解耦契约：SessionRecord（交互历史）、WorkspaceVersion（版本化工作区）、TaskCheckpoint（任务恢复）、AuthorizationFence（每次执行前及恢复后重检权限）、ExecutionLedger（幂等键、外部回执、对账状态）。ToolDispatcher必须在持久记录意图后才发起副作用，超时进入UNKNOWN并先查询外部状态而非盲目重试。

优先演练：①响应丢失但外部写入成功；②撤权与恢复并发；③客户端取消后后台仍在执行；④Sandbox故障重建；⑤多Agent并发修改同一工作区。度量重复副作用率、越权次数、p99停止/恢复延迟、每成功任务总成本；不要把模型Token吞吐当作生产可靠性。

## 情报与预测质量

11月16日采集快照在撰稿时缺失；最近11月15日快照显示19/19信源抓取成功、84条候选、666条跨日未核验积压；独立Gold样本为0，重要事件召回率不可计算。RSS候选与Sitemap lastmod均未经独立核验。两条2027-03-31到期的已登记预测保持原条件和概率，不提前判YES/NO。长期KG未满足高质量实质更新门槛，今日仅提交空Delta。

## 官方 Sources

- LangGraph Releases：https://github.com/langchain-ai/langgraph/releases
- LangGraph.js Releases：https://github.com/langchain-ai/langgraphjs/releases
- NVIDIA OpenShell release qualification：https://github.com/NVIDIA/OpenShell/milestone/10
- Codex Releases：https://github.com/openai/codex/releases

> 证据边界：本期为有限一手抽查与历史对照，不是全行业穷尽审计；版本日期按官方发布记录，Sitemap lastmod不作发布日期。
