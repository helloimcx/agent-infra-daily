---
layout: post
title: "Agent Infra Daily · 2026-10-06"
date: 2026-10-06 23:59:00 +0800
summary: "OpenShell 打通 Sandbox Supervisor 与 Gateway 的 OTLP trace context；LangGraph 修复旧 checkpoint 上 replay 污染其他分支的问题，提醒 Durable Execution 需要 branch isolation。"
tags: [agent-infra, observability, openshell, durable-execution, langgraph, security]
---

## 今日最重要进展

### OpenShell 将 trace 从 Gateway 延伸到真正运行 Agent 的 Supervisor

[NVIDIA OpenShell #3977](https://github.com/NVIDIA/OpenShell/commit/d1e8f44a062a) 于北京时间 10 月 6 日早间合入。Gateway 开启 OTLP 导出时，会经 Kubernetes、Docker、Podman、VM 等 compute driver 将端点及启动操作的 W3C `TRACEPARENT` 传给 sandbox supervisor；supervisor 以 `openshell-supervisor` 服务名导出 span，关联 sandbox ID，退出前 flush。启动链路覆盖 image-policy discovery、policy load、boundary attach、agent start 和 access start；egress connect 则拆成 authorize、resolve、dial 等子操作。

此举解决了传统 tracing 的关键盲区：API Gateway 接到 `create` 后，真正耗时可能发生在 driver、sandbox 内 policy attach 和进程启动；若没有跨边界 trace，调用方看到的只是黑盒等待。需留意高频 egress trace 的采样与成本，单靠 tracing 不能替代保留明确归属的审计日志。该提交证明了实现路径，不证明所有部署均正确启用 OTLP exporter 或保留全部 span。

### LangGraph 修复“旧 checkpoint 重播污染其他分支”

[LangGraph #9170](https://github.com/langchain-ai/langgraph/commit/2d942085e214) 修复对已经被线程推进过的 update/fork checkpoint 执行 replay 时，写入旧 checkpoint 并被其已存在的子分支读取的问题。提交例子显示 `DeltaChannel` 可观察到本不属于该分支的写入；`Command(update=...)`、`Command(goto=...)` 的重播也可能反复进入其他分支。

这里的失败并不是普通重试出错，而是 **history isolation**：checkpoint DAG 上一个已有多个后代的节点，不应该在新 replay 时继续接受会被后代继承的变更。正确做法是明确 fork 的写入归属，避免历史分支被后来操作静默污染。这是长期 Agent 回放、调试与并行分支的基础数据一致性要求。

## 新项目 / 版本

当天 OpenShell 还合入了 [provider multiple tokens per request](https://github.com/NVIDIA/OpenShell/commit/8579dfb30194)（2026-10-05 23:15 UTC），增强单次请求的凭据处理灵活性。它应视为实现能力迭代，不应被扩展为“不需要 Credential Broker”或“凭据无泄漏保证”。LangGraph 同日有 [1.2.13](https://github.com/langchain-ai/langgraph/commit/8e15e0d0bcff) 和 [1.2.14](https://github.com/langchain-ai/langgraph/commit/70dd64065bff) 发布提交：版本号代表项目迭代，但长期知识更新重点仍应以可检验的恢复语义变化为主。

## 论文 / 研究

未核实到本时间窗内需要新建 Research Entity 的重大一手论文。当天有价值的实验材料主要是 repo 内针对 checkpoint fork、DeltaChannel 重播的定向回归测试，不应混称外部 benchmark。

## 趋势判断

**Observability 越来越需要跨 gateway、driver、sandbox 与外部动作链路。** 单点 server span 不足以解释用户视角的失败时延；Trace ID 必须与 sandbox ID、operation generation 和 credential decision 关联。

**Durable Runtime 的正确性开始更多暴露在重播数据结构上。** Step journal 不只是持久化结果；checkpoint DAG、channel update 的归属、branch fork 和序列化顺序都可能左右实际状态。对基于 checkpoint 的 Agent，更要测试多分支历史回放，不应只测试单线 restart。

## 工程启示

1. 定义 Gateway operation span → driver span → Supervisor startup span → egress authorize/resolve/dial 的跨边界 trace propagation；W3C traceparent 与 sandbox/execution ID 并用。
2. 对高频出站请求实施可配置采样、span budget 与安全字段脱敏，避免把敏感凭据写入 telemetry。
3. 为 checkpoint DAG 制定不可变历史语义：在旧 checkpoint replay/修改时创建新 fork，严禁写回可被旧后代消费的位置。
4. 测试并行分支、interrupt/resume、Command(update/goto)、DeltaChannel 重建后的 **branch non-interference**。
5. 不从 OTLP tracing 或 checkpoint replay 的存在推断 exactly-once 外部副作用。

## Sources

- OpenShell — Supervisor OTLP traces：https://github.com/NVIDIA/OpenShell/commit/d1e8f44a062a
- LangGraph — fork before replay on past checkpoint：https://github.com/langchain-ai/langgraph/commit/2d942085e214
- OpenShell — multiple provider tokens per request：https://github.com/NVIDIA/OpenShell/commit/8579dfb30194
- LangGraph — release 1.2.13：https://github.com/langchain-ai/langgraph/commit/8e15e0d0bcff
- LangGraph — release 1.2.14：https://github.com/langchain-ai/langgraph/commit/70dd64065bff
