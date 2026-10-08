---
layout: post
title: "Agent Infra Daily · 2026-10-08"
date: 2026-10-08 15:12:00 +0800
summary: "Anthropic 推出独立 srt-proxy 与外部 decider 路径；Open SWE 合入异步任务协调及 Cloud/Mac thread handoff；OpenShell 修复滚动升级中的 supervisor reconnect 与 Ready 状态窗口。"
tags: [agent-infra, sandbox, network-policy, agent-harness, cloud-agent, high-availability]
---

## 今日最重要进展

### Anthropic 将 HTTP Proxy / Decider 从本机 Sandbox 中抽离

[Anthropic sandbox-runtime srt-proxy](https://github.com/anthropics/sandbox-runtime/commit/c6d5baa6867e) 在北京时间 10 月 8 日早间合入，随后经 [PR #666](https://github.com/anthropics/sandbox-runtime/commit/3f0bad734523) 合入主线。新增 `srt proxy` 独立运行方式：工作负载可以部署在别处，proxy 通过外部 decider 的 length-prefixed JSON 协议获取每个请求的 verdict。决策包含 allow（可做 header 改写和可选单请求 credential）、deny 或 request body first。decider 失联、超时或 protocol violation 时拒绝请求，且 decider 退出后 proxy 退出。它显式区分了执行位置和网络授权位置。

与此同时，[per-command network allow lists](https://github.com/anthropics/sandbox-runtime/commit/8f8623ee7c50) 和 [filterRequest request rewriting](https://github.com/anthropics/sandbox-runtime/commit/69dfe3bb5c3c) 为 scoped policy 添加 deny reason、请求标准化及 opt-in 的 tunnel/host 防护。后者说明若存在未经 inspection 的 opaque tunnel 或 Host/SNI 不一致，同一份“允许域名”规则可能被旁路，因此必须把 tunnel 行为放入 threat model。部分限制是 opt-in，默认并未全部开启，不应误称默认就获得所有防护。

### Open SWE 开始将多 Agent 工作组织成 Coordinator 与 Asynchronous Workers

[Open SWE #3658](https://github.com/langchain-ai/open-swe/commit/1483d1e8cd6f) 合入 task coordinator 与 asynchronous workers：协调器可以委派任务，由后台 worker 独立推进，并把结果/事件记录在 transcript。重要边界是此功能带有 **default-off preference**，并不是所有现有线程默认进入多 Agent 模式。变更专门关注 worker follow-up、untrusted task output delimiters、worker cancellation 后不自动唤醒等语义。

同日的 [Cloud 与 This Mac 线程移交](https://github.com/langchain-ai/open-swe/commit/fdb69cb0d10b) 和 [离线后转云端](https://github.com/langchain-ai/open-swe/commit/1006aff4a0b0) 方向，开始将“用户在哪台设备”与“Agent 线程的长期身份”解耦。这不是 VM live migration 的声明；它关心的是 thread/context、workspace 状态和执行位置的明确 handoff，必须单独验证未提交改动、凭据与本地工具绑定。

### OpenShell 发现并修复 gateway pod roll 的实际 HA 窗口

[OpenShell #4321](https://github.com/NVIDIA/OpenShell/commit/9b5bcdd7a291)（2026-10-08 05:18 UTC）修复两类导致客户端看到 `sandbox is not ready` 的问题。Supervisor 曾在成功建立 session 后未重置 reconnect backoff，连续滚动升级会把重连延迟累积到最大 30 秒；此外旧 gateway 发出 redirect 后立刻将 sandbox 从 Ready 降到 Provisioning，而接管 replica 还没有确认 replacement session。修复包括重置 backoff，并在确实发出 redirect 的情形等待最多 5 秒以观察 replacement，再决定降级状态。

这提供一个很好的反例：有 consistent hashing、有 session redirect，也不等于用户无感 HA。状态何时可被标记 Ready、哪个实例有权降级、重连退避何时重置，都直接决定实际可用性。

## 新项目 / 版本

Anthropic `srt-proxy` 是已有 sandbox-runtime 的新运行模式，不作为全新独立供应商项目计数。Open SWE 新增异步协调/Handoff 功能，但仍应按合入代码与 opt-in 边界记录，不提前视为稳定商业 SLA。OpenAI Agents SDK 的 [conversation session write batching](https://github.com/openai/openai-agents-python/commit/26345c1e45eb) 处理 API 写入上限，属于长对话存储工程修复。

## 论文 / 研究

本时间窗口截至北京时间 15:12，没有找到需要新建 Research Entity 的可信一手重大发表。以上均为可核查的工程实现进展，不将 release notes 或回归测试冒充论文成果。

## 趋势判断

1. **Policy Decision Plane 可以与 Execution Plane 物理分离。** 独立代理 + 外部 decider 使异构 sandbox、远程 Agent、浏览器服务共享中心化 HTTP 判定成为可能；代价是 decider 高可用、请求延迟和 fail-closed 可用性权衡。
2. **Multi-Agent 不是只有 subagent API。** 背景 worker 要有 durable ownership、取消、事件归属、不可信输出边界与唤醒条件；否则异步协作极易变成幽灵任务与上下文串线。
3. **Cloud↔Local handoff 与 HA session handoff 是不同层面。** 前者转移用户工作的执行位置；后者迁移同一 sandbox 的网络控制会话。两者都要求显式身份，但不可合并为一个“迁移成功”布尔值。

## 工程启示

- 架构分离 `Agent Thread ID`、`Task/Worker ID`、`Sandbox ID`、`Gateway Session Owner` 与 `Policy Decision ID`，使用 trace/correlation 串联，避免生命周期强耦合。
- `Policy Proxy -> External Decider` 采用严格超时、fail-closed、Host/SNI/目标地址校验和拒绝原因审计；为高频请求设计可控 cache 与 latency SLO，但缓存不可破坏 credential scope。
- 异步 worker 的 task event 只回到其启动线程；取消后抑制过期 completion；从 worker 回流的自然语言与工具结果都按不可信输入处理。
- Cloud/Mac handoff 先定义 workspace dirty state、credentials、network locality 与当前 side-effect window 的 transfer/abort 规则，再谈用户无感切换。
- HA 测试至少注入多次 gateway roll、旧 session redirect 已发出但新 session 尚未建立、重复 reconnect 与 stale Ready/Provisioning 状态，核对客户端错误率而不是只看 pod Ready。

## Sources

- Anthropic — srt-proxy external decider：https://github.com/anthropics/sandbox-runtime/commit/c6d5baa6867e
- Anthropic — merge PR #666：https://github.com/anthropics/sandbox-runtime/commit/3f0bad734523
- Anthropic — per-command allowlists：https://github.com/anthropics/sandbox-runtime/commit/8f8623ee7c50
- Anthropic — request filter and bypass controls：https://github.com/anthropics/sandbox-runtime/commit/69dfe3bb5c3c
- Open SWE — coordinator and async workers：https://github.com/langchain-ai/open-swe/commit/1483d1e8cd6f
- Open SWE — Cloud/This Mac handoff：https://github.com/langchain-ai/open-swe/commit/fdb69cb0d10b
- Open SWE — This Mac offline cloud routing：https://github.com/langchain-ai/open-swe/commit/1006aff4a0b0
- OpenShell — HA pod roll readiness：https://github.com/NVIDIA/OpenShell/commit/9b5bcdd7a291
- OpenAI Agents Python SDK — conversation session write batching：https://github.com/openai/openai-agents-python/commit/26345c1e45eb
