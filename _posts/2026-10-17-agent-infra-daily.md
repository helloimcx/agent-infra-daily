---
layout: post
title: "Agent Infra Daily · 2026-10-17"
date: 2026-10-17 08:16:00 +0800
summary: "OpenShell 可插拔隔离后端、Open SWE 托管 Agent Loop、LangGraph Resume 正确性、ADK 压缩隔离与 Codex 插件信任绑定。"
tags: [agent-infra, sandbox, durable-execution, cloud-agent, security, harness]
---

## 今日最重要进展

**1. OpenShell #3898：可插拔 Isolation Backend RPC（10 月 17 日 03:18，北京时间）。** Operator 注册内置或外部隔离后端，Compute Driver 向 Supervisor 传递受控启动信息，协议显式表达 Unix socket、固定地址候选 TCP 和 VSOCK。补丁包含外部 V8 示例与 conformance tests。重点是安全后端可以替换，但选择权不应落到 Agent 工作负载；接口存在不等于所有实现安全等价。

**2. Open SWE #4159：Agent 与 Reviewer 统一迁移 Managed Deep Agents（10 月 17 日 03:53）。** 删除按线程在本地与远端 Runtime 之间选择的兼容路径，MDA_RUNTIME_URL 成为必要配置；托管端运行模型循环，原 Backend 通过签名 Run Token 提供工具与业务能力。后续 #4180 进一步统一 Graph 执行。此变更不能证明运行中线程支持无损热迁移。

**3. LangGraph #9265 / #9322：并行 Resume 完成事实与写入索引（10 月 17 日 02:33 / 00:07）。** 非法人工恢复输入不再立即取消其他 sibling，先等待在途任务完成再传播错误，减少外部副作用发生后又被重跑的窗口。另一补丁调整特殊 writes 保存顺序，避免 Command(resume, update) 的更新被重复应用。这些是局部恢复一致性改进，而不是外部 exactly-once 保证。

**4. Google ADK：Context Compaction 按 isolation_scope 隔离（10 月 17 日 03:45）。** token 估算、最近压缩记录和事件重建按当前任务隔离域过滤，防止子 Agent 的压缩状态串用。#20a5a0c 同日修复 GCS Skill 资源路径穿越：统一相对路径、Windows 路径与 realpath containment 校验。

**5. Codex #54619：Plugin Hook 执行前校验插件内容（10 月 16 日 22:38）。** Command Hook 和 MCP Hook 都在运行前执行 plugin_trust.verify()，校验时间计入原超时预算。审批必须绑定具体插件内容，而非仅绑定插件名称。#54664 又区分 Thread Store 可安全重试错误与写入结果未知，但不会自动重试。

**6. OpenHands #5955：先获得 Run Slot，再写入会话消息（10 月 17 日 06:03）。** Gateway 在并发配额耗尽时先返回 429，避免客户端重试在已有会话里重复追加用户消息。Admission 顺序本身成为持久状态正确性的一部分。

## 新项目 / 版本

LangGraph 发布 1.2.16（10 月 17 日 06:02），Python SDK 发布 0.4.8（06:01）。OpenShell #4320（05:48）新增经 Supervisor session 下发 Gateway 配置的路径，尚需验证断连与配置代际。Anthropic sandbox-runtime 发布 v0.0.80（10 月 17 日 01:18）；版本发布本身不构成新的安全保证。

## 论文 / 研究

本窗口重点核验了源码、合入提交与发布记录，未发现可据此建立独立 Research Entity 的新增高质量论文及可追溯 benchmark，不凑数。

## 趋势判断

**隔离后端协议化、模型循环托管化、恢复语义并发化。** 这些趋势来自不同项目的代码级增量，是本站综合分析，不是单一厂商的统一承诺。可插拔后端要求外部信任根，远端模型循环要求独立任务与授权身份，恢复正确性要求非法输入不能破坏其他任务的完成事实。

## 工程启示

对百万用户 Cloud Agent，显式记录 BackendRegistrationVersion、SandboxGeneration、RunToken、TaskCompletionID、ApprovalAttemptID 与 CompactionScope。针对后端重连、无效 Resume、插件内容变更、429 配额拒绝、跨 scope 压缩分别做故障注入。外部工具操作必须区分已执行、未执行和结果未知；客户端超时不是重试许可。

## Sources

- OpenShell Isolation Backend RPC: https://github.com/NVIDIA/OpenShell/commit/77929d9c1469068417825768c798dd81bd0e0d08
- OpenShell Gateway config push: https://github.com/NVIDIA/OpenShell/commit/604b9f66f685c582114cd571ae3a10accec23ec2
- Open SWE MDA migration: https://github.com/langchain-ai/open-swe/commit/4550c8c6f39d4e92b3bea787eb84f2ee781763d5
- Open SWE all graphs on MDA: https://github.com/langchain-ai/open-swe/commit/ab4104b7fa6a
- LangGraph invalid resume: https://github.com/langchain-ai/langgraph/commit/b0cabd93d05508d246318c92b41b3952fe56f5c3
- LangGraph Command update: https://github.com/langchain-ai/langgraph/commit/e14f4277dc43e1d12981a36c02757fbec6ede217
- LangGraph 1.2.16: https://github.com/langchain-ai/langgraph/commit/41c9c22fdc83
- LangGraph SDK 0.4.8: https://github.com/langchain-ai/langgraph/commit/51018652a6c7
- Google ADK compaction isolation: https://github.com/google/adk-python/commit/dd9ca6fc100c146978ce2d199ff168458be4007b
- Google ADK Skill path traversal: https://github.com/google/adk-python/commit/20a5a0cd47735487b504a249a3145cea5d4afef3
- Codex plugin trust: https://github.com/openai/codex/commit/2bf2bdf82c33f4c66ba3f0767b8e4b6a933aac40
- Codex Thread Store outcome: https://github.com/openai/codex/commit/96eb400d1231f0199e96f640c740096087cf3e9b
- OpenHands Run Slot admission: https://github.com/OpenHands/software-agent-sdk/commit/4a5f5a09096aea331b91481a5ff94dbfed22940e
- Anthropic sandbox-runtime release: https://github.com/anthropics/sandbox-runtime/commit/626a59671ee2
