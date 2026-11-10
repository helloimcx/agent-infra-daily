---
layout: post
title: "Agent Infra Daily｜2026-11-10：前沿模型升级与分层 Agent 执行成本"
date: 2026-11-10 08:00:00 +0800
summary: "Anthropic 发布 Fable/Mythos 5.2，推动高难度任务模型路由；百万用户 Agent 应按任务风险与成本分层，不能以厂商自测替代生产验证。"
tags: [agent-infrastructure, model-routing, cloud-agent, security, research]
---

# 今日核心判断

**高能力模型与低成本执行层的分工正在变得更明确，但模型能力突破并不自动解决百万用户 Agent 的授权、状态持久化和成本控制。** 过去约24小时最重要的一手信号是 Anthropic 于 2026-11-09 公布 Claude Fable 5.2 / Mythos 5.2。另一个值得对照的背景是近期 LangGraph 的严格恢复和客户端重连修复，二者分别处于模型能力层与执行可靠性层，不能混为一谈。

## 重大进展与证据边界

**1. Claude Fable 5.2 / Mythos 5.2 正式公布（11月9日，官网日期）。** Anthropic 表示二者为同一底层模型，Fable 带有更严格的网络安全与生物安全防护、面向一般用户；Mythos 通过特定验证计划开放。官网标价常规模式每百万输入/输出 Token 分别为 $8/$40，快速模式 $16/$80，宣称输出生成速度相对 5.1 最多提升30%，快速模式最高可达2.5倍。官网建议日常任务优先使用 Opus 5.5，将 Fable/Mythos 用于更高难度任务，并支持 Advisor/Orchestrator 角色。**边界：**速度与 Benchmark 均来自厂商披露，不是独立生产测量；特定任务与努力级别不能跨基准直接比较。官方日期为美国网站11月9日，未独立确认精确北京时间发布时刻，故不推断小时级事件时间。

**2. 多 Agent 并行规模出现新的厂商实验样本。** Anthropic 描述一个使用逾1,000个子 Agent、持续8天的原型操作系统实验，以及约1,000 Agent、30小时形式化费马大定理证明的实验。它们证明厂商已在探索大规模协作，但不是可复用的百万用户 SLA、单位任务成本或跨租户隔离证据。**工程反证要求：**需看到可复现的调度开销、任务完成率、失败恢复、上下文一致性与权限边界。

**3. 严格恢复机制继续作为独立基础设施需求。** LangGraph 1.2.20（11月5日）为 interrupt 分配独立 ID，并拒绝过期恢复答案；SDK 0.4.14（11月6日）暴露 strict_resume。它们属于此前已发布的稳定更新，**不是今日新品**。严格恢复解决审批状态一致性，不提供外部操作 Exactly-once 保证。

## 厂商路线与 Tradeoff

Anthropic 的 Advisor/Orchestrator 方向强调高难度模型负责规划、审查与关键决策，较小模型负责可拆解任务；优点是按复杂度分配能力，代价是路由误判、协作 Token、重复工作和权限传播。LangGraph 更强调工作流中断与恢复一致性；OpenShell/AgentCore 等运行时方案则关注沙盒生命周期、会话隔离及审计。**没有单一产品覆盖模型推理、持久任务、工具授权、业务幂等的全部语义。**

## 标准与研究

今天未独立确认新的 P0 级 Agent 协议标准正式生效。模型厂商的性能与安全评估是重要研究线索，但其自测分数、案例和用户评价应分别标记为厂商评测/示例/外部证言，不能升格为独立 Benchmark 或生产采用率。

## 7 / 30 天趋势雷达

- **加强（7天）：** 模型分层路由、严格恢复和工具副作用治理的工程必要性，证据来自不同技术层。
- **加强但待证实（30天）：** 多 Agent 协作可完成更复杂工程任务；生产成本与恢复可靠性尚缺独立可复验结果。
- **待证实：** 高能力模型担任 Advisor 是否比单模型端到端运行降低每个成功任务的总成本。
- **未发现可确认推翻：** 现有独立 Tool Gateway、Durable Runtime、Workspace Store 的分层设计仍有必要。

## 百万用户 Cloud Agent：下一步实验

优先构建 **Risk-aware Model Router + Execution Ledger**：入口按任务难度、敏感度和预算选择小/中/高能力模型；高风险操作通过服务端授权网关和审批版本检查；外部副作用由独立账本记录幂等键、请求、回执和对账状态；沙盒和上下文缓存允许丢失但任务 Checkpoint 与 Workspace 必须可恢复。做 A/B 测试时同时比较成功任务成本、Token、TTFT p95/p99、失败恢复、重复执行与人工审查时间；按复杂度分层，不以厂商 Benchmark 直接推导业务收益。

## 数据质量与知识维护

截至本次读取，2026-11-10 的 intel/daily 快照尚不存在。最近 2026-11-09 快照为 19 个配置源中 18 个成功、deepmind-blog 解析失败、42 条当期候选、456 条跨日未核验候选；独立 Gold 样本数 0，无法计算召回率。队列中的候选未经核验，Sitemap lastmod 不代表事件日期。长期 KG 不因本次模型发布自动增加实体；对应 Delta 四组空数组。两条目标日 2027-03-31 的预测维持原条件与概率，不提前判 YES/NO。

## 官方 Sources

1. Anthropic, *Claude Fable 5.2 and Mythos 5.2*, 2026-11-09: https://www.anthropic.com/claude-fable-and-mythos-5-2
2. LangGraph Python Releases: https://github.com/langchain-ai/langgraph/releases
3. LangGraph.js Releases（恢复与流式状态对照）: https://github.com/langchain-ai/langgraphjs/releases
