---
layout: post
title: "Agent Infra Daily · 2026-10-14"
date: 2026-10-14 08:38:00 +0800
summary: "OpenShell 分层变更锁与 Error 恢复、Codex 后台压缩一致性、Agents SDK 审批保护、Google ADK Sandbox 隔离及 Open SWE MCP 治理。"
tags: [agent-infra, durable-execution, sandbox, mcp, concurrency, security]
---

## 今日最重要进展

**OpenShell #4147：从全局串行锁转向分层控制面变更锁。** 10 月 14 日 07:34（北京时间）合入的变更将 global/workspace/sandbox 意向锁按冲突域划分；PostgreSQL advisory lock 使用独立的四连接池和统一的约十秒截止时间，锁竞争超时映射为 `UNAVAILABLE/MUTATION_LOCK_TIMEOUT`。provider 删除时重新核验引用、credential refresh 早退清理 staged handles、启动 endpoint 对账按 sandbox 分页加锁并有限重试。默认每 replica 数据库连接预算由 10 增至 14，不能只看到吞吐提升而忽略连接上限。原有 legacy global key 仍保证滚动升级中旧 replica 与新锁体系互斥。该提交的 PostgreSQL 专项测试有独立运行入口，不能推断所有场景已由常规 CI 覆盖。

**OpenShell #4231：错误 Sandbox 允许受控 stop/start 恢复。** 10 月 14 日 07:50 合入。基础设施 Error 不必永远成为终态，但操作员应先修复原因、执行 stop、等待旧计算资源清理成功后再 start。持久 workspace 可以保留，旧 SSH session 随执行代际失效；timeout cleanup 仍可能拥有回收所有权。恢复必须先解决资源归属，再考虑重试。

**Codex #53800：后台 Compaction 接入 Turn 生命周期。** 10 月 14 日 07:51 合入。pre/mid/post-turn 检查点可启动异步上下文压缩；候选结果必须校验历史前缀和客户端路由，采纳时保留新增消息、工具输出及 world-state 更新。前台 turn 取消不再自动杀掉已运行的 session-owned 候选；若采纳后仍超预算则可回退一次前台压缩。关键在于历史变换的版本一致性，而不是摘要是否生成成功。

**OpenAI Agents SDK #5363：待决审批不能被自动压缩吞掉。** 10 月 14 日 04:36 合入。Hosted MCP approval 尚未完成时延后自动 compaction，并保留 request/response 的身份配对。Human-in-the-loop 的待决授权是执行状态，不是可随意裁剪的聊天文本。

## 新项目 / 版本

**Google ADK：Sandbox 环境适配与跨会话绑定修复。** 10 月 14 日 06:12 的提交新增 `OpenSandboxEnvironment`，通过 `BaseEnvironment` 和 `EnvironmentToolset` 统一命令执行、文件 I/O 与资源生命周期；样例默认五分钟 TTL、使用期间续期、toolset 关闭时销毁。几乎同时合入的另一个修复将共享 `AgentEngineSandboxComputer` 的 session resources 从实例字段迁到 asyncio task-scoped `ContextVar`，防止并发 prepare() 使 A 会话调用落到 B 的 sandbox。前者是可替换执行后端，后者是跨租户归属正确性，二者不能互相替代。

**Open SWE #4050：Managed MCP Gateway 统一到 Instance。** 10 月 14 日 08:00 合入。管理员统一选择 LangSmith Managed Tools gateway，workspace 不再单独覆写；用户仍需自己的 service grant。连接页面列出已连接和缺失服务；共享缓存以配置 generation 失效，存储读取失败的 fallback 不再写入缓存。这是产品治理实现，不是 MCP wire protocol 的新版标准。

## 论文 / 研究

本次研究窗口内未核验到足以建立独立 Research Entity 的一手论文机制增量，因此不添加未经复核的研究节点或 benchmark 数字。本日重点是可复查的控制面和 Harness 代码变更。

## 趋势判断

第一，Cloud Agent 的控制面开始从“单个锁保证安全”走向 **按资源归属分区、跨版本兼容、可诊断的并发治理**。第二，Context Compaction 已经是并发状态变换，必须像 checkpoint 一样管理历史版本、授权待决状态和候选采纳。第三，Sandbox 的 session binding、资源 TTL 与业务任务持久化正在形成不同的职责平面。第四，企业 MCP gateway 的统一 catalog 不应意味着统一用户 credential。

## 工程启示

对百万用户 Cloud Agent，建议建立 `TaskID / SandboxID / WorkspaceID / Generation / ApprovalID / ToolCallID` 及资源租约映射。控制面按 global/workspace/sandbox 定义冲突域并监控 lock wait P95、连接池饱和和超时分类；Sandbox Error 恢复执行 stop/cleanup/start 栅栏；模型上下文压缩记录 source-history revision，审批未完成时保留原始授权请求；执行网关在 task-local 绑定之外再次校验 user/session/sandbox/lease。MCP 管理分离实例目录、用户 grants 与缓存 generation。以上是本站架构建议，不代表上述项目均已实现完整方案。

## Sources

- OpenShell scoped mutation guards: https://github.com/NVIDIA/OpenShell/commit/e30c938bb159322d5018b9c261c001c658f40071
- OpenShell Error sandbox recovery: https://github.com/NVIDIA/OpenShell/commit/b4baf23db38889e22d3e7cb3eea85490ba4a2a44
- Codex async compaction: https://github.com/openai/codex/commit/9e03960cf8807c37fc987bf17b4e745b8b3339d2
- OpenAI Agents SDK approval compaction: https://github.com/openai/openai-agents-python/commit/5eb47a5bdeab8ba9f6087de288c7e606816c76c6
- Google ADK sandbox resource binding: https://github.com/google/adk-python/commit/facaf297b1f7f74516f090df03e10eae0808bd56
- Google ADK OpenSandbox environment: https://github.com/google/adk-python/commit/69d1c901ba842b5300d6ef8ce2872ea545b2375c
- Open SWE instance MCP gateway: https://github.com/langchain-ai/open-swe/commit/d1ada86e352cf406b1c07dbefd5275c53a407604
