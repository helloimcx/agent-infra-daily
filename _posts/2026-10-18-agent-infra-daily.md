---
layout: post
title: "Agent Infra Daily · 2026-10-18"
date: 2026-10-18 08:39:00 +0800
summary: "ADK 循环 Join 依赖栅栏、OpenHands 子 Agent 与 Lease fencing、Open SWE MCP 来源可追溯、Codex WebSocket 压缩及 ADK 错误分类。"
tags: [agent-infra, orchestration, durable-execution, mcp, security, observability, cloud-agent]
---

## 今日最重要进展

研究窗口：北京时间 2026-10-17 08:21 至 2026-10-18 08:39。下列提交按 GitHub 上游提交时间（UTC+8）核验，代码合入不等于正式生产可用。

**1. Google ADK：循环 JoinNode 改为每轮依赖栅栏（10 月 17 日 15:05）。** [a6ed859](https://github.com/google/adk-python/commit/a6ed85905d4c1d1f285ba9d4f76a9d801b66d17f) 引入按 JoinNode 记录的 `join_arrivals`，每次触发后清空，下一轮必须重新等到全部前驱。旧逻辑可能把上轮 B1 与本轮 A2 混合，生成跨迭代的错误输出。无输出节点还会清除旧 `node_outputs`。这解决的是 DAG 内迭代的依赖因果，不等于外部工具 exactly-once。

**2. OpenHands：新增可替换的子会话启动器（10 月 17 日 17:03）。** [#5126](https://github.com/OpenHands/software-agent-sdk/commit/5966c781ed014efc96c028a99bddd4ff78426741) 新增 `start_child_conversation` Tool 与 `POST /api/conversations/{id}/children`，默认在父会话所在后端创建子会话，继承配置与 Workspace，并可选择独立 Git worktree 或共享目录；外部托管后端可以替换 launcher。子 Agent 不自动获得父会话的完整聊天历史，必须通过自包含 task brief 传递目标。**控制面需要显式记录 parent/child 身份、隔离选择、配额和取消级联。**

**3. OpenHands：Lease Ownership Lost 必须拒绝且不留下幽灵状态（10 月 17 日 09:13）。** [#5973](https://github.com/OpenHands/software-agent-sdk/commit/f621dab57be854aaee3a982c83b6bf34b8ce5705) 将失去会话写入权的错误映射到 HTTP 409，并让 `save_meta` 先完成受保护的持久化，随后才更新内存元数据。原先可能出现磁盘拒绝但内存已改的状态分叉。**Fencing 必须保护写入事实和可见状态；它不自动撤销已发生的外部副作用。**

**4. Open SWE：MCP Tool Catalog 增加无凭据来源证明（10 月 17 日 11:36）。** [#3747](https://github.com/langchain-ai/open-swe/commit/d177a79fbdd33f5f695bbdb38f611f9851b7ed74) 在工具发现中增加 `connection_name`、`scope`（instance/workspace/user/managed）和 `overridden_scopes`，解释同名工具最终来自哪一层连接；测试确保不会把 token 与内部 Gateway ID 泄露到目录。**可见 provenance 不能替代调用时动态授权。**

**5. Codex：App-server WebSocket 引入协商式 zstd-stream（10 月 18 日 04:54，07:34 加入功能开关）。** [#54930](https://github.com/openai/codex/commit/8d9f6466ff0294785d56f55b1fe363d132fe4133) 要求升级请求与响应均携带 `x-codex-app-server-compression: zstd-stream-v1`，否则保持原 JSON text 协议。双向各自维护连续压缩流，单条消息 flush、不结束 frame，重连重新建流，并限制解压后大小；[#54949](https://github.com/openai/codex/commit/7b44ac1661433ae3a6f375fde873fa7123c935fe) 将其置于 feature flag 下。**这是传输优化而非 durable stream：断线后压缩字典和业务回放位置均不能沿用。**

**6. Google ADK：工具失败从异常扩展到结果语义（10 月 17 日 13:47、13:49）。** [a4b8ee9](https://github.com/google/adk-python/commit/a4b8ee94c8dcbcd867fe41567868413ae6b834c1) 与 [6a77d48](https://github.com/google/adk-python/commit/6a77d48cc6405cd50a33c87e1b533881ebf72380) 统一了观测插件的 ToolResultClassifier：MCP `isError` 或应用定义的错误返回，即使没有抛异常也计入工具失败；同一失败在 on_tool_error 与 after_tool 两阶段避免重复计数。模型 finish/block reason 与工作流节点故障分离，利于建立可靠的 Agent 质量指标。

## 新项目 / 版本

OpenShell [#4397](https://github.com/NVIDIA/OpenShell/commit/b58e24c9dabd6d4bcf2b7186592d3ad50646541b) 修复中间件将明文 HTTP/WS 错标为 HTTPS/WSS 的问题，影响请求上下文中的 scheme 语义。[#4677](https://github.com/NVIDIA/OpenShell/commit/fdfbf84f8b42e8b2d76fd5fc4d7479a7c9c410c5) 补齐 OCSF `device.os.type_id` 必填字段，增强事件 schema 兼容性。Open SWE [#4199](https://github.com/langchain-ai/open-swe/commit/d4efde8a18) 则让 queued-count 查询失败时仍能读取线程信息，降低控制面辅助统计故障对主查询的耦合。本轮没有发现足够重要且已核验的全新基础设施项目发布。

## 论文 / 研究

本窗口以合入代码、测试和官方仓库记录为主，未发现可确认在窗口内发布、具备足够独立机制或可复现 benchmark 的高质量新论文。本次不新建 Research Entity，也不编造性能数字。Codex 压缩补丁没有提供生产环境流量压缩率，不能把协议实现等同于成本改善的定量证据。

## 趋势判断

**从“功能支持”走向“代际正确性与来源可解释”。** ADK 的 Join arrivals、OpenHands 的 Lease fencing 与子会话隔离分别解决 DAG 迭代、写入所有权和多 Agent 资源归属；Open SWE 的 MCP provenance 则解决工具能力来源可解释性。这是跨项目代码的本站分析，不是厂商共同承诺。另一个信号是观测语义从异常计数演进到返回值分类与去重，便于可靠评测。

## 工程启示

对大规模 Cloud Agent，建议在执行日志显式携带 `TaskId`、`IterationId`、`JoinGeneration`、`ConversationLeaseGeneration`、`ParentConversationId`、`MCPConnectionScope` 与 `ToolCallId`。分别故障注入：Join 前驱跨轮交错、旧 Worker Lease 失效后的写入、子 Agent worktree 与共享目录混用、MCP 目录缓存与撤权竞态、WebSocket 断线重连、工具错误回调重复。不要把 WebSocket 压缩状态、模型生成续接、任务 checkpoint 和外部副作用回执合并为一个 resume token。

## Sources

- Google ADK JoinNode loop barrier: https://github.com/google/adk-python/commit/a6ed85905d4c1d1f285ba9d4f76a9d801b66d17f
- OpenHands child conversation: https://github.com/OpenHands/software-agent-sdk/commit/5966c781ed014efc96c028a99bddd4ff78426741
- OpenHands ownership fencing: https://github.com/OpenHands/software-agent-sdk/commit/f621dab57be854aaee3a982c83b6bf34b8ce5705
- Open SWE MCP provenance: https://github.com/langchain-ai/open-swe/commit/d177a79fbdd33f5f695bbdb38f611f9851b7ed74
- Codex zstd WebSocket: https://github.com/openai/codex/commit/8d9f6466ff0294785d56f55b1fe363d132fe4133
- Codex compression flag: https://github.com/openai/codex/commit/7b44ac1661433ae3a6f375fde873fa7123c935fe
- Google ADK tool classification: https://github.com/google/adk-python/commit/a4b8ee94c8dcbcd867fe41567868413ae6b834c1
- Google ADK logging plugin integration: https://github.com/google/adk-python/commit/6a77d48cc6405cd50a33c87e1b533881ebf72380
- OpenShell plaintext scheme: https://github.com/NVIDIA/OpenShell/commit/b58e24c9dabd6d4bcf2b7186592d3ad50646541b
- OpenShell OCSF schema: https://github.com/NVIDIA/OpenShell/commit/fdfbf84f8b42e8b2d76fd5fc4d7479a7c9c410c5
