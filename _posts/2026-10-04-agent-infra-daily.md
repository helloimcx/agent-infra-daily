---
layout: post
title: "Agent Infra Daily · 2026-10-04"
date: 2026-10-04 09:17:00 +0800
summary: "OpenShell 把 Sandbox provisioning 从同步 RPC 推向持久化分布式操作：阶段 deadline、operation ownership、late-result fencing 与 launch-signing preflight 成为今天最值得关注的 Runtime 增量。"
tags: [agent-infra, runtime, sandbox, security, openshell]
---

## 今日最重要进展

### OpenShell 正在补齐 Sandbox Control Plane 的“Durable Provisioning”语义

过去约 24 小时里，最有工程含量的增量来自 NVIDIA OpenShell。10 月 3 日合入的 [#4038](https://github.com/NVIDIA/OpenShell/commit/8983642e280e7b0f2ed423edbffd705ef259e7c0) 不只是普通 timeout 修复：它把 sandbox image preparation 与 admission 拆成两个独立 deadline，并把阶段状态跨 gateway restart 持久化；create/start 请求在 caller cancellation、monitor failure 或 preparation timeout 后仍保留 pending provisioning ownership，driver 返回后再决定 cleanup，同时对旧 operation 的 late result 做 fencing，并加入 ordered multi-replica regression。

这意味着 Sandbox Runtime 的可靠性边界正在从“VM/container 能不能隔离 Agent”继续下沉到“控制面能不能正确管理一次跨秒级/分钟级、可能超时和重入的资源创建操作”。对 Cloud Agent 来说，这很关键：上层 Task 即使有 Durable Execution，如果底层 sandbox create/start 因超时、gateway 重启或多副本竞态留下 orphan compute，任务恢复仍然是不完整的。

同一天的 [#4034](https://github.com/NVIDIA/OpenShell/commit/71c3cd957abef062eb7f37010056717cd49f2ed3) 又把 launch-signing validation 前移到 VM image preparation 之前，并要求 replacement VM credential 在停止 active compute 之前先验证。这个顺序变化体现的是 fail-before-side-effect：配置/签名错误应在昂贵准备、持久化或停机动作之前暴露，而不是进入补偿路径后再失败。

此外还有一组相互呼应的可靠性修复：[#4039](https://github.com/NVIDIA/OpenShell/commit/4188eabaf2d41fbf94f7d793f411af21b3a4685b) 在清理 staging files 前停止 image workers；[#4036](https://github.com/NVIDIA/OpenShell/commit/d676e036a47e5bcffde8230a2a79ea43d14e47ff) 拒绝冲突的 workload identity selectors；[#3772](https://github.com/NVIDIA/OpenShell/commit/e7d14edd884fe1feaa806dd01089da34ba2fdcd5) 修复 target 先关闭时 outbound relay stream 的关闭语义。这些改动共同指向：OpenShell 当前的主要演进已经不只是 policy surface，而是开始处理真实分布式 Runtime 的生命周期边角。

## 新项目 / 版本

过去 24 小时没有发现值得单独进入知识图谱的新 Agent Infra 项目或重大正式版本。MCP specification 仓库在窗口内只有依赖维护提交；Docker Sandbox Kit、Restate 等已跟踪核心项目没有发现同等级别的新架构增量。因此今天不为“保持日报数量”而引入薄节点。

OpenShell 0.1.5 milestone 仍在推进，当前 issue 集中在 IPv6/DNS egress、NAT64-aware SSRF、OIDC CA trust、release security gate 等控制面/安全细节。今天的合入更适合视为 0.1.5 前后的工程硬化信号，而不是一个新的产品发布。

## 论文 / 研究

过去约 24 小时未发现达到本知识库门槛、且相对现有 Mid-Harness / AREX-2 / SIFT 产生实质新结论的一手 Agent Harness / RSI 论文。今天不新增 Research Entity。

这本身也是一个有用的筛选结果：日报应把“没有新论文”与“复述过去一周论文”区分开，避免 evidence stream 被重复内容稀释。

## 趋势判断

### 1. Sandbox 正在从 Execution Primitive 变成 Stateful Control-plane Resource

早期 Agent Sandbox 讨论主要围绕隔离技术：container、gVisor、microVM、启动速度和 filesystem。OpenShell 这组改动显示更成熟的实现会很快遇到 Kubernetes/controller 类问题：operation identity、phase deadline、ownership、reconciliation、fencing、compensation 与多副本一致性。

这意味着未来评估 Sandbox 平台时，仅比较“启动 200ms 还是 2s”已经不够。至少还要问：

- create/start 是否有稳定 operation identity？
- caller cancellation 是否会错误中断已经提交的资源操作？
- gateway/control-plane crash 后能否恢复 pending operation？
- late driver result 会不会覆盖新一轮操作？
- cleanup 是否有 ownership/fencing，避免错误删除新资源？
- preparation、admission、boot 是否共享一个粗粒度 timeout？

### 2. Task Durability 与 Infrastructure Durability 必须分层但对齐

Restate 类 Durable Execution 解决的是任务 step/journal；OpenShell 这次暴露的是 sandbox resource lifecycle。两者不能互相替代。

一个更完整的 Cloud Agent Runtime 应该至少存在两条状态机：

**Task state machine**：RUNNABLE → RUNNING → WAITING → COMPLETED/FAILED。

**Execution resource state machine**：PREPARING → ADMISSION → PROVISIONING → READY → CLEANUP。

它们通过 stable execution/sandbox identity 对齐。否则上层“恢复成功”可能只是重新发起了一次底层资源操作，造成重复 VM、workspace 错配或错误补偿。

### 3. Fail-before-side-effect 会成为 Agent Control Plane 的通用设计原则

Launch signing 在 image preparation 前验证、replacement credential 在 stop active compute 前验证，本质都是把确定性错误尽量推到副作用之前。

这个原则同样适用于 Agent tool execution：policy、credential scope、schema、quota、approval requirement 能在真正调用 SaaS、部署、删除或支付之前验证的，都不应该拖到 side effect 之后再靠补偿修复。

## 工程启示

如果正在设计百万用户 Cloud Agent / Agent Sandbox 服务，今天最值得直接吸收的不是某个 OpenShell API，而是一组控制面不变量：

1. **Persist ownership before dispatch**：先记录谁拥有 operation，再调用异步 driver。
2. **Separate phase deadlines**：镜像准备、准入、启动不要共享一个无法诊断的总 timeout。
3. **Caller lifecycle ≠ resource lifecycle**：HTTP/gRPC caller 消失不代表底层 VM 创建已经停止。
4. **Fence late results**：每次资源变更需要 generation / operation token，旧结果不能修改新状态。
5. **Cleanup is also an operation**：补偿删除必须有 ownership，不能看到 timeout 就无条件 DELETE。
6. **Preflight before destructive side effects**：credential/signing/policy/host-tool validation 尽量前移。
7. **Trace detached workers**：异步 handoff 后仍保留 parent trace，否则最难排查的 provisioning 故障恰好失去链路。

## Sources

- NVIDIA OpenShell — provisioning deadlines and durable ownership: https://github.com/NVIDIA/OpenShell/commit/8983642e280e7b0f2ed423edbffd705ef259e7c0
- NVIDIA OpenShell — launch signing preflight: https://github.com/NVIDIA/OpenShell/commit/71c3cd957abef062eb7f37010056717cd49f2ed3
- NVIDIA OpenShell — stop image workers before staging cleanup: https://github.com/NVIDIA/OpenShell/commit/4188eabaf2d41fbf94f7d793f411af21b3a4685b
- NVIDIA OpenShell — reject conflicting workload identity selectors: https://github.com/NVIDIA/OpenShell/commit/d676e036a47e5bcffde8230a2a79ea43d14e47ff
- NVIDIA OpenShell repository: https://github.com/NVIDIA/OpenShell
