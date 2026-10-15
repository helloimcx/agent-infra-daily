---
layout: post
title: "Agent Infra Daily · 2026-10-15"
date: 2026-10-15 08:12:00 +0800
summary: "LangGraph checkpoint pruning、OpenShell OCSF OTLP、ADK 并行工具恢复、Codex MCP OAuth 失效、Open SWE Managed Deep Agents 与 OpenHands 孤儿回收。"
tags: [agent-infra, durable-execution, sandbox, observability, mcp, cloud-agent]
---

## 今日最重要进展

**LangGraph checkpoint-postgres #9290（10 月 15 日 03:09，北京时间）**：PostgresSaver 和 AsyncPostgresSaver 新增 `prune`，支持 `delete` 和 `keep_latest`。后者保留每 namespace 最新 checkpoint、pending writes 和引用 blobs；对依赖祖先增量的 DeltaChannel 明确拒绝不安全裁剪。随后发布 checkpoint-postgres 3.2.0。持久状态的 retention 必须先证明可恢复，不能直接按时间删除祖先。

**OpenShell Gateway + Supervisor OCSF → OTLP Logs（10 月 15 日 03:04/03:50）**：#4500 将 Gateway OCSF 事件映射为 OTLP 日志并支持旧 schema 降级；#4545 将该路径扩展到 Sandbox Supervisor，Collector 配置经受控 driver 传递，认证头使用脱敏包装。OTLP 接入不等于安全审计无损，Collector 故障和字段降级必须对账。

**Google ADK 并行恢复（10 月 14 日 09:34、10 月 15 日 07:15）**：ReplaySequenceBarrier 缓存提前完成的节点，等待前驱完成后按序释放；并行工具 batch 中某 sibling 抛错时，已完成的工具响应事件不再被丢弃。前者解决 replay 排序，后者解决部分成功结果可见性；两者都不能证明外部副作用 exactly-once。

**Codex MCP OAuth #54079（10 月 15 日 04:00）**：服务端明确拒绝 refresh token 后，客户端退休旧刷新资格，并防止异步取消或并发重新登录使旧回调覆盖新凭据。永久拒绝、暂时网络故障和新授权必须是不同状态。

**Open SWE #4053（10 月 15 日 02:33）**：agent 与 reviewer 模型循环可在 Managed Deep Agents 托管部署执行，通过签名 run token 回调原 Open SWE backend 工具。实验开关只作用于新线程，不代表支持既有线程热迁移。

**OpenHands #5774（10 月 15 日 02:59）**：Agent Server 重启时依据持久 run record、进程组和 Linux /proc 启动时间清理 Canvas backend 孤儿进程。主进程退出不等于工具服务已释放，跨主机仍需 lease 与 generation fencing。

## 新项目 / 版本

LangGraph checkpoint-postgres 3.2.0 新增明确的历史清理 API；Open SWE Managed Deep Agents 为实验性远端运行选项。本日其他变化主要是已合入代码的可靠性与安全修复，不夸大为生产 GA。

## 论文 / 研究

没有完成符合本日时间窗口与一手证据要求的新论文核验；不新增 Research Entity 或未经核实的 benchmark。

## 趋势判断

Agent Runtime 的可靠性正在从“有 checkpoint”深化到“可安全裁剪、可因果回放、可记录部分成功”。同时模型循环、工具执行与安全事件采集开始独立部署。分层越清晰，越需要跨层的稳定身份、审计与恢复协议。

## 工程启示

百万用户 Cloud Agent 应把 Thread、Run、ToolCall、SandboxGeneration、CredentialGrant 作为独立身份；为 checkpoint/channel 明确 retention 和 replay 依赖；为并行工具保存单调用结果与副作用凭证；在 MDA 回调中验证签名和 run generation；将 OCSF 事件完整性与普通 Trace SLO 分开；重启时对账残留执行资源。这些是本站架构建议，而非各项目已经统一实现的事实。

## Sources

- LangGraph prune: https://github.com/langchain-ai/langgraph/commit/36bf3887f074f2b05f42409c8a67e3a33ed1d1ba
- LangGraph release: https://github.com/langchain-ai/langgraph/commit/d4149cc1f538
- OpenShell Gateway OCSF: https://github.com/NVIDIA/OpenShell/commit/07fd2386ce18fb4e6312b695909d612ffeae578d
- OpenShell Supervisor OCSF: https://github.com/NVIDIA/OpenShell/commit/6dbe4adc56e5c7f60b96010b41fe21caba0872a8
- ADK replay barrier: https://github.com/google/adk-python/commit/a4ba8137262f6a36339f6dd02f41cf9710f8542f
- ADK parallel results: https://github.com/google/adk-python/commit/7d3658ef1a1f61c4c18cc4781f6892460add960c
- Codex OAuth: https://github.com/openai/codex/commit/4ae6016a93880877f8f5f79a64e462c466d6b3f9
- Open SWE MDA: https://github.com/langchain-ai/open-swe/commit/9dd9fbea0ea06e6c583126d8c5e5176171527830
- OpenHands orphan reaping: https://github.com/OpenHands/software-agent-sdk/commit/91b89bdc6f33d185a1da85e9da54c521e53fcdec
