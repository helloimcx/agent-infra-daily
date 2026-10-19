---
layout: post
title: "Agent Infra Daily · 2026-10-19"
date: 2026-10-19 08:19:00 +0800
summary: "Open SWE Monitor 后台事件、Codex 模型请求级 Hook、Google ADK 动态子节点 Retry、OpenHands Webhook 计时器恢复及 Agent 控制面改进。"
tags: [agent-infra, cloud-agent, orchestration, observability, durable-execution, coding-agent]
---

## 今日最重要进展

研究窗口：北京时间 2026-10-18 08:39 至 2026-10-19 08:19。下列时间均依据上游 GitHub commit 时间（UTC+8），代码合入不等于生产可用。

**1. Open SWE：长期后台 Monitor 事件化（10 月 18 日 11:55）。** [#4196](https://github.com/langchain-ai/open-swe/commit/d306285cea768680f0802d7e8b8247825916f377) 增加 `monitor(start/output/stop/list)`：Sandbox 运行长时命令，编号保存原始输出，过滤后的行经回调提示或约一分钟轮询投递到线程。Background Work 面板显示 Monitor 与 background_execute。Monitor 工具默认关闭，需要用户开启实验开关；filter 本身是可执行 Shell，也被纳入 PR 创建与 Workflow Push 守卫。**工程启示：** 后台命令、事件投递和 Agent 主 Turn 应是独立生命周期，需监控投递游标与缺口。

**2. Codex：模型请求级只读 Hook（10 月 19 日 06:43）。** [#55144](https://github.com/openai/codex/commit/70b3bb6d8814ab3f2045238b4ae14c43da99783b) 增加 `PreModelRequest` / `PostModelRequest`，对每次请求尝试（含重试）记录模型、会话、Turn、可选子 Agent、完成/失败/取消和可得 Token Usage。同步后置 Hook 在工具派发前等待，异步 Hook 允许流式工具派发继续；Hook 输出不能否决请求或修改模型上下文。**工程启示：** ModelRequestAttempt、Turn 与 ToolCall 不可合并为单一观测事件。

**3. Google ADK：动态子节点 Retry 快照（10 月 18 日 15:17）。** [e2dbc0f](https://github.com/google/adk-python/commit/e2dbc0f55027372f3a701d41004ee006ee8f9f14) 为每次父节点尝试保存子节点运行计数快照，失败后只回滚到本次尝试起点。回归测试覆盖第一次子结果被父节点拒绝、第二次子节点失败、第三次必须重新执行的情形。**工程启示：** ParentAttemptId 与 ChildRunId 决定可重放结果的因果归属，计数恢复不能替代外部副作用幂等。

**4. OpenHands：Webhook 失败重排队的 Flush Timer 活性（10 月 18 日 12:33）。** [#6046](https://github.com/OpenHands/software-agent-sdk/commit/0b51554da5baa94fbd0b7919eec6a610fdbe93ec) 修复旧 timer 在 POST 期间看到空队列后退出、POST 随后失败重新入队却再无发送机会的竞态。失败后重新安排 timer。**工程启示：** 队列有事件不代表最终会投递，必须跟踪最老缓冲事件年龄、timer 状态及 Sink Ack。

**5. OpenHands：运行中的 /run 快速返回冲突（10 月 18 日 12:37）。** [#5954](https://github.com/OpenHands/software-agent-sdk/commit/59b2831c17fbd6793f1cb8103d3fd91e57420324) 先检查 live run task，避免第二次 /run 请求等待长工具调用持有的状态锁直至超时。客户端可及时得到 409 并 join 现有运行。

**6. Codex：迟到 Agent Mail 唤醒空闲根会话（10 月 18 日 09:58）。** [#54961](https://github.com/openai/codex/commit/8c076942cb70fba8e5c4732c23f1faabc4aed484) 新增默认关闭的 `wake_on_agent_messages`，允许已给出最终回答的根会话在收到子 Agent 消息时开启新 Turn；中断、Plan 模式和子 Agent 不自动唤醒。

## 新项目 / 版本

Open SWE [#4216](https://github.com/langchain-ai/open-swe/commit/aa00dc83871b11e134d30565e7901d4b8ae3ed1f) 让新线程在创建时直接归属 Managed Deep Agents，旧 local 线程仍按原 Runtime 服务并记录警告，不进行未经验证的热迁移。[#4209](https://github.com/langchain-ai/open-swe/commit/30d974acb2b8e2fb239f71057790ed940a69c10d) 允许通过 MCP 发起私有 Slack PR Review Channel，必须验证 GitHub PR 读取权与 Slack 身份，拒绝时不发送 DM 或创建频道。OpenHands [#6072](https://github.com/OpenHands/software-agent-sdk/commit/6ae64079cfd30cfe2f01a060c59168a4d650d883) 增加 ghu_/ghs_/gho_ GitHub Token 的日志脱敏。上述是已有项目的代码增量，未核验到需要独立建 Project Entity 的全新产品。

## 论文 / 研究

本窗口可靠证据集中于合入代码与回归测试，未核验到满足发布时间和机制独立性要求的新论文或可信 Benchmark，因此不编造吞吐、延迟和成本收益数字。

## 趋势判断

**Agent 长任务正在从单一循环分化为后台工作、请求尝试、动态子执行与观测投递四种生命周期。** Open SWE Monitor、Codex 请求 Hook、ADK 尝试快照和 OpenHands Webhook 修复分别揭示事件生成、执行归属和投递活性之间的边界。此为本站跨项目分析，并非厂商联合承诺。

## 工程启示

对大规模 Cloud Agent，建议区分 `TaskId`、`ParentAttemptId`、`ChildRunId`、`ModelRequestAttemptId`、`ToolCallId`、`MonitorId`、`MonitorSeq`、`DeliveryCursor`、`SinkAckId`。故障注入覆盖父节点连续拒绝后的重试、同步 Hook 阻塞工具派发、Monitor callback 与 polling 重复、Webhook POST 失败后 Timer 消失、长工具调用期间重复 /run，以及根会话完成后收到子任务结果。

## Sources

- https://github.com/langchain-ai/open-swe/commit/d306285cea768680f0802d7e8b8247825916f377
- https://github.com/openai/codex/commit/70b3bb6d8814ab3f2045238b4ae14c43da99783b
- https://github.com/google/adk-python/commit/e2dbc0f55027372f3a701d41004ee006ee8f9f14
- https://github.com/OpenHands/software-agent-sdk/commit/0b51554da5baa94fbd0b7919eec6a610fdbe93ec
- https://github.com/OpenHands/software-agent-sdk/commit/59b2831c17fbd6793f1cb8103d3fd91e57420324
- https://github.com/openai/codex/commit/8c076942cb70fba8e5c4732c23f1faabc4aed484
- https://github.com/langchain-ai/open-swe/commit/aa00dc83871b11e134d30565e7901d4b8ae3ed1f
- https://github.com/langchain-ai/open-swe/commit/30d974acb2b8e2fb239f71057790ed940a69c10d
- https://github.com/OpenHands/software-agent-sdk/commit/6ae64079cfd30cfe2f01a060c59168a4d650d883
