---
layout: post
title: "Agent Infra Daily · 2026-10-07"
date: 2026-10-07 23:59:00 +0800
summary: "LangGraph 解决 exit-durability 恢复时 DeltaChannel 重复或错序回放；OpenAI Agents SDK 修复审批恢复的函数调用历史缺口；OpenShell 增强 Supervisor 会话多副本路由。"
tags: [agent-infra, durable-execution, replay, sessions, openshell, orchestration]
---

## 今日最重要进展

### LangGraph 把“恢复后回放顺序”提升到可测试的正确性条件

[LangGraph #9114](https://github.com/langchain-ai/langgraph/commit/3a1796ecf072)（2026-10-06 22:05 UTC）指出：exit-durability 的并行 interrupt 后恢复，会把部分已写入 checkpoint 的 `DeltaChannel` writes 再次写入，出现重复；直接删除重复项又会造成排序错乱。提交提供最小对照：live 顺序为 `['in1','p','r']`，恢复后错误顺序可成为 `['in1','p','r','p']`。原因在于已载入的 task write 被重新赋予以 step 为前缀的任务 ID，而排序规则让旧 ID 与新 ID 发生语义错位。

修复将“哪些 writes 是此前已经存在、哪些是本轮新产生”纳入 replay 与 checkpoint 的明确规则。对长期运行 Agent 来说，**恢复成功 ≠ 最终状态正确**；恢复后不得多执行、少执行、错序应用状态增量，也不能让真实发生的决策序列和展示给用户的事件序列分叉。

### OpenAI Agents SDK 修复审批恢复后的 Session 历史缺口

[openai-agents-python #4828](https://github.com/openai/openai-agents-python/commit/c757a4346214)（2026-10-06 18:27 UTC）揭示一个具体故障窗口：在 output guardrails / 非默认 tool-use behavior 下，被中断轮次的 function_call 延迟写入；用户审批后恢复时可能只持久化新产生的 function_call_output，却丢掉配对的 call。后续 Responses API 会以 `No tool call found for function call output` 拒绝运行。修复在继续执行的恢复路径中写入 deferred prefix，再记录解决后的新消息，涵盖 streamed/non-streamed 两条路径；再次中断仍保留 defer。

这个案例说明 Agent Session 不只是 chat transcript，而是具备跨中断因果约束的事件日志。记录输出而未记录所属调用，会让持久数据成为后续运行的非法状态。

### OpenShell Supervisor 多副本路由引入 consistent hashing

[OpenShell #3661](https://github.com/NVIDIA/OpenShell/commit/834b79a8c235)（2026-10-07 05:01 UTC）为 supervisor session 引入一致性哈希分配、gateway shutdown handoff 与连接转发，并提供可选 per-replica GRPCRoute。目的不是让所有连接“任意实例都处理”，而是使长连接找到当前所有者，并在成员变化时可定向迁移。发布后仍需要专门验证 pod roll、owner 退出与 reconnect backoff 等边界，不能据此宣称零中断 HA。

## 新项目 / 版本

Go MCP SDK 当日合入 [token expiry before required scopes](https://github.com/modelcontextprotocol/go-sdk/commit/8dd5d6a7e126)，安全检查顺序变得更明确。OpenShell 同一天还有 [SSH host identity persistence](https://github.com/NVIDIA/OpenShell/commit/9fd41e6bfd0a)（2026-10-06 20:09 UTC）以及 [uninspected credential binary scope](https://github.com/NVIDIA/OpenShell/commit/360c5a02cba5)（2026-10-06 20:27 UTC）的安全相关修订。没有足够证据称这些改动构成一个新的统一协议发布。

## 论文 / 研究

未核实到本日新的高价值 Agent RSI/long-horizon 论文正式发布。今天的一手价值集中在可复现的失败案例与合并的回归代码，不能把三组不同工程测试合并成一份性能 benchmark。

## 趋势判断

**长期 Agent 的正确性开始从“任务能跑完”转向“恢复保持历史因果一致性”。** DeltaChannel 排序、tool-call 与 tool-output 配对、长连接 ownership 看似分属不同技术栈，底层共同点是：状态必须有稳定 identity、明确归属、重建规则和跨版本兼容约束。

**Cloud Agent 的控制面不能全面无状态化。** API front door 可以无状态，但 supervisor session、审批等待、checkpoint DAG 都有独立持久身份。应该外显这些对象，而不是依赖一个进程活着或同一条 websocket 一直在。

## 工程启示

1. Agent Session 事件落盘要维持 `tool_call -> tool_result` 的引用完整性，审批恢复时先恢复 deferred prefix，再持久化后续结果。
2. 针对 `interrupt -> resume -> retry -> stream` 建立因果与事件排序测试；验证重启后的状态不仅可读取，而且和不重启时等价。
3. Gateway 使用一致性哈希/显式所有权管理长连接；需要独立测试成员变化、redirect、重连超时和双 owner 风险。
4. 对每次恢复记录原始 checkpoint/branch、task attempt、owner generation 以及恢复目标版本，便于 replay 差异定位。
5. 凭据审计分别验证 token expiry、scope 和 resource audience，而不是把通过一项校验误解成完整授权。

## Sources

- LangGraph — exit-mode DeltaChannel replay ordering：https://github.com/langchain-ai/langgraph/commit/3a1796ecf072
- OpenAI Agents SDK — persist deferred approval history：https://github.com/openai/openai-agents-python/commit/c757a4346214
- OpenShell — supervisor session consistent hashing：https://github.com/NVIDIA/OpenShell/commit/834b79a8c235
- Go MCP SDK — check token expiry before scopes：https://github.com/modelcontextprotocol/go-sdk/commit/8dd5d6a7e126
- OpenShell — persist sandbox SSH host identity：https://github.com/NVIDIA/OpenShell/commit/9fd41e6bfd0a
- OpenShell — require full binary scope for uninspected credentials：https://github.com/NVIDIA/OpenShell/commit/360c5a02cba5
