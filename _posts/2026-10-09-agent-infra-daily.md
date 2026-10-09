---
layout: post
title: "Agent Infra Daily · 2026-10-09"
date: 2026-10-09 08:10:00 +0800
summary: "Gemini agent、OpenShell 策略匹配、LangGraph 恢复语义与 Open SWE 状态迁移。"
tags: [agent-infra, cloud-agent, policy, sandbox, durable-execution]
---

## 今日最重要进展

**Google Gemini agent（10 月 8 日）。** Google Cloud 官方宣布跨设备共享记忆、持续运行的长期 Agent：可处理定时任务与事件，动态创建临时子 Agent，长期 coworker 拥有独立 Workspace 账号和存储。身份、OAuth 授权、Sandbox 网络边界、Agent Gateway、审计与项目预算暂停组成企业控制链。这是产品架构声明，尚非 checkpoint、迁移或 exactly-once 的公开实现证明。

**OpenShell 策略一致性（10 月 9 日 07:52 北京时间）。** #4336 修复 Rust route matcher、Rego endpoint selector 与形式化 Prover 对 glob 路径的语义差异，补充一致性和反例重放测试。REST allow rule 仍使用不同匹配规则。#4313 改进 Proposal 审计，展示全部 endpoint 和允许规则，而非只展示第一项。Policy 的执行、验证与审计视图必须同义。

**LangGraph 人工恢复（10 月 9 日 03:59 北京时间）。** #9232 修复非法 `interrupt(response_schema=...)` 输入在 ToolNode 内被吞成普通工具错误的问题，并确保 `GraphInterrupt` 正确传播。无效人工输入不应丢失等待中的中断；异常类型保持兼容，但暂停行为变化需回归测试。

## 新项目 / 版本

Open SWE #3792 将个人设置和凭据迁到 PostgreSQL，以导入进度与行锁协调多副本；#3793 将 Skills 和 thread blobs 迁移，并采用后台分页导入。Google ADK 修复重复 confirmation 可能导致工具再次执行的问题。OpenAI Agents SDK 加固 macOS 本地沙箱，但原生端到端验证仍待完成。

## 论文 / 研究

未核验到需要新增 Research Entity 的一手论文；本日主要是可复查的工程代码增量。

## 趋势判断

长期 Agent 的身份、任务、工作区、worker、权限与预算正分离。安全策略要验证不同解释器的语义一致性。人工审批的核心是恢复与幂等，不是对话 UI。云端 Agent 数据迁移必须兼容滚动升级的混合版本。

## 工程启示

为 Agent、Task、ToolCall、Approval、Sandbox、PolicyVersion 建立独立 ID；人工审批状态机保留非法输入的待审批态，重复确认必须幂等；对策略验证器、执行器和审计输出进行差分测试；数据库迁移使用进度游标、行锁、延迟清理旧存储；预算暂停与等待审批应释放昂贵执行资源。

## Sources

- Google: https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026
- OpenShell: https://github.com/NVIDIA/OpenShell/commit/b959bb68179504bd517ad2d23866b391620c68ff
- OpenShell audit: https://github.com/NVIDIA/OpenShell/commit/fe2dd3e9d047
- LangGraph: https://github.com/langchain-ai/langgraph/commit/5965d72ff7d1
- Open SWE: https://github.com/langchain-ai/open-swe/commit/880a8ca74b02
- Open SWE: https://github.com/langchain-ai/open-swe/commit/09a2529ff21b
- ADK: https://github.com/google/adk-python/commit/bfdeb4a1ed74
- Agents SDK: https://github.com/openai/openai-agents-python/commit/125efa029b4b
