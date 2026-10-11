---
layout: post
title: "Agent Infra Daily · 2026-10-11"
date: 2026-10-11 08:54:00 +0800
summary: "LangGraph 输入增量归属、Google ADK 并行 HITL 屏障、Anthropic AF_VSOCK 沙盒封堵与 OpenHands 初始化门禁。"
tags: [agent-infra, durable-execution, hitl, sandbox, security, cloud-agent, replay]
---

## 今日最重要进展

**1. LangGraph 修复 DeltaChannel 输入增量的 checkpoint 祖先归属（10 月 10 日 19:57，北京时间）。** [#9258](https://github.com/langchain-ai/langgraph/commit/b4991f1ba36a2449ab59c38ab71828ee865bff84) 解决 `update_state(..., as_node="__input__")` 把写入保存在“新 checkpoint 自己”而不是“被更新 checkpoint 祖先”的问题。DeltaChannel 的读取依赖祖先写入，因此原行为会让当前 checkpoint 无法回放输入；后续 snapshot 甚至可能固化缺失。补丁统一了 node/input 写入路径，处理旧 checkpoint fork 的独立 snapshot，并给手动写入的消息补稳定 ID。此前的 [#9257](https://github.com/langchain-ai/langgraph/commit/6aa0afba682b0308fbcace31f66fb532978d4dca) 同期修复 InMemorySaver 缺省 checkpoint ID 时的增量历史读取。这是 checkpoint *归属语义* 的实质修复，不是跨存储后端 exactly-once 证明。

**2. Google ADK 修复并行人工审批的在途任务取消（10 月 11 日 03:26，北京时间）。** [ParallelWorker 修复](https://github.com/google/adk-python/commit/531a86a194c910ec5bfdfc9f7de09be80c5aaada) 将 `NodeInterruptedError` 从致命异常中分离：某个并行分支请求人工输入后，停止派发新任务，但等待已启动 sibling worker 完成并保留结果，再把整体状态转为 WAITING。随后 [rehydration 修复](https://github.com/google/adk-python/commit/bcac35a6efb21f176eef9d28d663db247f4e5afd) 区分直接中断与后代中断：`rerun_on_resume` 节点必须等自己的全部直接审批答复到齐才能重跑，而父节点可在子节点部分解除阻塞后推进。两次提交共同明确了并行 HITL 的 drain barrier 与多审批恢复边界。

**3. Anthropic sandbox-runtime 封堵 Linux VM socket 出站旁路（10 月 11 日 05:15，北京时间）。** [#691](https://github.com/anthropics/sandbox-runtime/commit/5507fb0e639c00f845554336ece62e27af5b1bb7) 在 seccomp 中拒绝 `socket(AF_VSOCK, ...)`，因为 network namespace 不能限制 VM sockets，可能绕过代理直接触及宿主环境。测试覆盖 socket 类型及 EPERM，并保留 AF_INET 行为。**边界提示：**`allowAllUnixSockets=true` 在 Linux 也会放开 AF_VSOCK；继承 FD、SCM_RIGHTS 等并不因这一 syscall 规则自动解决。

**4. OpenHands Agent Server 强化 deferred-init 入口门禁（10 月 11 日 08:12，北京时间）。** [#5700](https://github.com/OpenHands/software-agent-sdk/commit/f824a949af7f8045cc6691d7945ce7b31bfe9606) 将 `require_initialized` 前置于认证，覆盖 workspace、bridge、API 和 WebSocket，并加入并发初始化与真实连接测试；其前置 [#5661](https://github.com/OpenHands/software-agent-sdk/commit/c4b93299cf2b31c8b5d0b2c5a89965ccc5ff24f9) 先补上未初始化时的 socket 与 /v1 门禁。端口监听和鉴权可用不等于执行环境 READY，初始化期间的入口必须拒绝任务。

## 新项目 / 版本

- [Codex #52937](https://github.com/openai/codex/commit/6c0c6759d061) 让客户端显式标记的命名工具输出在 context compaction 后按 token budget 保留或整体丢弃，避免重要工具证据被无差别裁剪；需注意这是有条件保留，不是无限持久记忆。
- [Codex #52972](https://github.com/openai/codex/commit/de8fab6d7adfcef8b4ce6f02f3b5c8be4092015a) 升级 Rust MCP SDK `rmcp` 至 3.5.1，并调整生命周期测试；属于协议客户端兼容性维护，不代表 MCP 规范版本变化。
- [Open SWE #3917](https://github.com/langchain-ai/open-swe/commit/a91e0203fe2d34afdc60cf43e0e662c5160e6a30) 扩展远程 MCP 暴露的 human/expedited review 工具，并为 MCP 上下文调整描述模板。外部 Agent 可以调用工具，但审核身份与 PR owner 规则仍必须在服务端验证。
- [Open SWE #3939](https://github.com/langchain-ai/open-swe/commit/c879adc8d981) 修复 automation run 对 thread 的读取权限；是自动化任务与线程授权边界的补丁，不是新调度框架。

## 论文 / 研究

本轮核验范围内，未找到同时满足“近 24 小时实际发表、具有可复查机制增量、来源可靠”的新论文。**不新增 Research Entity，不编造 benchmark 数字。** 今日重点是一手代码与针对性回归测试。

## 趋势判断

**Durable Runtime 的关键约束正在细化为“增量归属 + 并行审批屏障 + 生命周期入口”。** LangGraph 证明 checkpoint 祖先关系影响可回放性；Google ADK 证明暂停不是立即取消所有并行任务；OpenHands 证明初始化状态需要先于认证成为独立执行门禁。三者不等同于统一实现，却共同指向状态机正确性比“有 checkpoint、有队列、有容器”更重要。**Sandbox 安全也在从 HTTP 域名规则扩展到 syscall-family 与继承描述符边界**，必须审计网络命名空间之外的通信面。

## 工程启示

1. 为 `Task / Step / Checkpoint / WriteSet / Branch / Approval / WorkerLease` 建立独立身份。验证 `update_state`、旧 checkpoint fork、Delta snapshot、重启与恢复的等价性；checkpoint 成功并不能代替因果一致性验证。
2. 并行 HITL 引入 `RUNNING → DRAINING → WAITING` 屏障：中断后停止新派发、保留在途结果，超时则触发 fencing 和可重试状态；多审批需区分直接与后代 interrupt ID。
3. 对 Linux Sandbox 建立 syscall egress matrix：`AF_UNIX`、`AF_VSOCK`、`AF_INET`、`io_uring`、继承 FD 与 socket passing 分开测试。允许 Unix socket 的配置必须显式接受 VSOCK 例外风险。
4. 将 Agent Server 的 `Liveness / Readiness / Initialization / CredentialAvailability` 分离。所有 HTTP、WebSocket、文件、bridge 入口必须经过同一 readiness gate；未就绪不接新任务，不能让认证错误掩盖初始化竞态。
5. Compaction 中保留的工具输出要有 provenance、budget、过期与脱敏策略；MCP 审批工具的远程调用必须在后端重新校验调用者、PR 与审批权限。

## Sources

- https://github.com/langchain-ai/langgraph/commit/b4991f1ba36a2449ab59c38ab71828ee865bff84
- https://github.com/langchain-ai/langgraph/commit/6aa0afba682b0308fbcace31f66fb532978d4dca
- https://github.com/google/adk-python/commit/531a86a194c910ec5bfdfc9f7de09be80c5aaada
- https://github.com/google/adk-python/commit/bcac35a6efb21f176eef9d28d663db247f4e5afd
- https://github.com/anthropics/sandbox-runtime/commit/5507fb0e639c00f845554336ece62e27af5b1bb7
- https://github.com/OpenHands/software-agent-sdk/commit/f824a949af7f8045cc6691d7945ce7b31bfe9606
- https://github.com/OpenHands/software-agent-sdk/commit/c4b93299cf2b31c8b5d0b2c5a89965ccc5ff24f9
- https://github.com/openai/codex/commit/6c0c6759d061
- https://github.com/openai/codex/commit/de8fab6d7adfcef8b4ce6f02f3b5c8be4092015a
- https://github.com/langchain-ai/open-swe/commit/a91e0203fe2d34afdc60cf43e0e662c5160e6a30
- https://github.com/langchain-ai/open-swe/commit/c879adc8d981
