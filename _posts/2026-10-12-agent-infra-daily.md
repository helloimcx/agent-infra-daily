---
layout: post
title: "Agent Infra Daily · 2026-10-12"
date: 2026-10-12 08:11:00 +0800
summary: "LangGraph 历史 checkpoint 分支隔离、Codex 冷恢复权限和连接绑定审批、OpenHands MCP 重连及孤儿进程清理。"
tags: [agent-infra, durable-execution, security, mcp, cloud-agent, sandbox]
---

## 今日最重要进展

**1. LangGraph 历史 checkpoint 分支隔离（10 月 11 日 20:51，北京时间）。** [#9269](https://github.com/langchain-ai/langgraph/commit/799c2f04fd3a56186e24e9fb8bbf3568e543cfbe) 在从已有后继的非最新 checkpoint 启动 `durability="exit"` 时强制 DeltaChannel snapshot，避免旧分支写入污染较新分支。测试覆盖一次和两次历史 fork 的 state history 对比。不同于昨天的输入祖先归属修复，这次针对**历史分支与新分支隔离**，不能外推为任意后端的分布式事务保证。

**2. Codex 冷恢复权限 Provenance（10 月 11 日 23:48）。** [#53150](https://github.com/openai/codex/commit/7c9bfb910ef65c8f4a957c53affbd43d5fac2882) 只从 thread-owned 历史快照恢复基础 permission profile、cwd 与 workspace roots，尊重当前 managed requirements、显式覆盖并过滤执行器临时 grants。Agent 的历史权限不是当前授权的替代品。

**3. Codex 连接绑定审批回复（10 月 11 日 14:08）。** [#53049](https://github.com/openai/codex/commit/8c0f7011674145da7e10627769fb221c74fbf7a0) 为 app-server 请求引入保留原 worker connection 与 request ID 的单次 reply handle。测试让两个 WebSocket 连接使用相同 ID，验证回复不会串线；AtomicBool 防止重复提交，但断线结果仍可能 unknown。这不是 MCP 规范更新。

**4. OpenHands MCP HTTP 重连（10 月 11 日 10:20）。** [#4838](https://github.com/OpenHands/software-agent-sdk/commit/4cc058275c5a08d845bd846576aafc80e5dd7d0d) 在 session task 已结束时锁内重置会话状态。测试首次 `tools/call` 返回 504、第二次使用同一工具对象恢复成功；第一次调用仍报错，不能据此安全重试非幂等写操作。

**5. OpenHands Canvas 后代进程清理（10 月 12 日 06:56）。** [#5689](https://github.com/OpenHands/software-agent-sdk/commit/c0471362d340ade1e334595ba98417108b415e88) 修复 backend leader 已退出但后代 HTTP 服务仍存活时的回收问题；状态查询、停止和重启会处理残余进程组。仅证明特定 manager 的恢复行为，不是跨平台沙盒隔离证明。

## 新项目 / 版本

- [Codex #53155](https://github.com/openai/codex/commit/95db2cd5d5f37f80affb9b50ce1de70ebb4513ff) 调整远程 app-server 关停顺序，在 WebSocket worker 结束前保持事件可投递，减少关停阶段丢通知风险。
- [Codex #53173](https://github.com/openai/codex/commit/27065a91ccbf) 增加受管后台服务的 TUI 重启能力，并核验 daemon 所有权；这是生命周期管理增强而非新调度框架。

## 论文 / 研究

未核验到本时间窗口内具有充分一手机制与实验数据的新论文。本日不新增 Research Entity 或 benchmark 数字，避免以未验证信息填充知识图谱。

## 趋势判断

**Agent 可恢复性的正确性边界正在细分为 checkpoint 分支归属、权限恢复来源、审批连接身份、工具会话恢复与进程组资源回收。** 这些问题来自不同实现，不能用单一 thread ID、一个 checkpoint 或一个 worker PID 统一解决。局部修复不是通用 exactly-once 的证据。

## 工程启示

1. Checkpoint 记录 branch generation 和写入归属；测试历史 fork、exit durability 与跨分支读取一致性，并测量 forced snapshot 的成本。
2. 冷恢复区分用户基础权限、受管策略、外来历史和临时 grants；重新校验 owner、撤权及显式降权。
3. 审批响应绑定 connection/generation + request ID，单次消费；发送失败时进入 UNKNOWN 并通过服务端 journal 对账。
4. MCP 会话重连与工具副作用幂等分层。HTTP 504 不证明写入未发生，非幂等工具应查询结果或使用幂等键。
5. Sandbox 释放前清理整个进程组并检查残余端口；无法回收时隔离 workspace，不允许立即复用。

## Sources

- https://github.com/langchain-ai/langgraph/commit/799c2f04fd3a56186e24e9fb8bbf3568e543cfbe
- https://github.com/openai/codex/commit/7c9bfb910ef65c8f4a957c53affbd43d5fac2882
- https://github.com/openai/codex/commit/8c0f7011674145da7e10627769fb221c74fbf7a0
- https://github.com/OpenHands/software-agent-sdk/commit/4cc058275c5a08d845bd846576aafc80e5dd7d0d
- https://github.com/OpenHands/software-agent-sdk/commit/c0471362d340ade1e334595ba98417108b415e88
- https://github.com/openai/codex/commit/95db2cd5d5f37f80affb9b50ce1de70ebb4513ff
- https://github.com/openai/codex/commit/27065a91ccbf
