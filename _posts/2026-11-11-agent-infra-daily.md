---
layout: post
title: "Agent Infra Daily｜2026-11-11：Sandbox 最小权限与取消语义"
date: 2026-11-11 08:00:00 +0800
summary: "Anthropic sandbox-runtime 与 LangGraph.js 近期正式更新显示，权限范围、网络代理与取消传播仍是 Cloud Agent 生产安全边界；未发现可独立确认的过去24小时P0标准变更。"
tags: [agent-infrastructure, sandbox, durable-execution, security, cloud-agent]
---

# 今日核心判断

**Agent 的安全边界不仅取决于启动时授予的权限，还取决于代理通道、取消传播和执行结束后的副作用。** 过去约24小时的独立检索未确认新的 P0 级 Agent 标准或通用生产能力发布；以下是两项有明确版本证据的 P1 进展，不将补丁版本夸大为行业转折。

## 重大进展与证据边界

**1. Anthropic sandbox-runtime v0.0.82（北京时间11月10日07:38，GitHub release）。** Windows 读取用户 Profile 的授权从整个目录缩窄到内置工具目录集合；非默认路径需要显式追加 grant。SOCKS 连接到 mitmProxy 目标域也会经过 MITM socket，TLS 客户端需信任代理 CA；HTTP 代理日志避免记录可能泄漏凭证的上游错误消息或堆栈。新增可选 Windows MXC BaseContainer 后端，要求 Node 24+ 与额外 SDK，MSYS2/Git Bash 尚不兼容。**边界：**这是正式发布的版本改进，不等于 Windows Sandbox 具备跨平台等价隔离，也没有公布多租户逃逸率或生产性能。

**2. LangGraph.js @langchain/langgraph 1.7.3（北京时间11月10日07:58，GitHub release）。** 当消费者退出 `for await` 流或取消 reader 时，运行将停止；此前仅显式 `stream.cancel()` 才会中止，可能让后台节点继续运行。另修正子图 namespace 精确匹配。配套 API 1.7.1 修正历史分页和 select 字段行为。**边界：**停止本地执行流不自动保证已经发出的远程工具请求被撤销，也不保证外部副作用回滚。

## 厂商路线与 Tradeoff

Anthropic sandbox-runtime 侧重操作系统级最小权限、网络代理及敏感日志边界；LangGraph 侧重任务流生命周期和执行状态；AgentCore/OpenShell 侧重托管执行隔离与控制面。前者更易精细约束本机工具但跨平台兼容成本较高；托管运行时更便于集中治理但存在控制面故障域与费用问题。应分别验证权限撤销、取消传播、外部调用对账，而不是以单一“Sandbox 安全”标签替代。

## 标准与研究

本次未确认过去24小时新的 MCP/A2A 正式标准生效。已有 MCP 工具注解不是可信授权依据；版本说明中的安全修复也不是独立攻防测评。对于 Windows MXC 后端，需等待兼容性与威胁模型验证，不能以可选实现等同生产成熟度。

## 7 / 30 天趋势雷达

- **加强（7天）：** 取消传播、严格恢复和最小权限的实现细节持续被修复。
- **加强但证据有限（30天）：** 运行时与工作流控制面分层，已有多个厂商实现，但尚缺统一跨后端恢复契约。
- **待证实：** Windows MXC 的隔离强度、兼容覆盖率及百万用户成本。
- **未确认推翻：** 仍需要独立的业务幂等账本和可信授权网关。

## 百万用户 Cloud Agent：具体工程建议

优先定义 **Cancellation & Permission Fence**：每次工具调用带 task_id、attempt_id、tenant_id、authorization_epoch、deadline、idempotency_key；取消后停止调度新步骤，正在执行的远程操作通过网关发送取消请求并记录确认/未知状态；对未知状态使用外部回执对账而非盲目重试。分别对 Windows/Linux 沙盒测试 Profile 文件访问、SOCKS/TLS 代理、错误日志脱敏、断线取消和成功执行但响应丢失。度量取消后仍发生的副作用、越权率、p99 停止延迟、单位成功任务成本；不虚构测试结果。

## 数据质量与知识维护

北京时间11月11日08时读取时，今日 `intel/daily/2026-11-11.json` 尚不存在。最近11月10日质量快照：19/19信源抓取成功、39条候选、490条跨日未核验候选；独立Gold样本0，无法计算重要事件召回率。候选未经核验，Sitemap lastmod不是事件日期。长期KG不因补丁版本自动增加实体，Delta四组空数组。两条2027年3月31日到期预测保持原条件和概率，未提前裁定。

## 官方 Sources

1. Anthropic sandbox-runtime v0.0.82: https://github.com/anthropics/sandbox-runtime/releases/tag/v0.0.82
2. LangGraph.js releases: https://github.com/langchain-ai/langgraphjs/releases
3. LangGraph Python releases (历史对照): https://github.com/langchain-ai/langgraph/releases
