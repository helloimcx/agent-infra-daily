---
layout: post
title: "Agent Infra Daily · 2026-10-05"
date: 2026-10-05 23:59:00 +0800
summary: "Anthropic sandbox-runtime 将 literal path 与 glob 区分为显式 policy 语义；OpenShell 增加网关每副本容量观测与可选 HPA，凸显权限解释正确性与控制面容量规划。"
tags: [agent-infra, sandbox, policy, security, openshell, observability]
---

## 今日最重要进展

### Anthropic Sandbox 的路径声明从“字符串约定”走向显式 Policy Semantics

北京时间 10 月 5 日凌晨合入的 [sandbox-runtime #621](https://github.com/anthropics/sandbox-runtime/commit/80a235195af5)（提交时间 2026-10-04 17:39 UTC）涉及 README、path entries、read-deny glob 及 Linux/macOS/Windows sandbox 后端，不是只修改文档。核心问题是用户指定的磁盘路径可能实际含有 `*`、`[` 等 glob 元字符，权限引擎不能仅凭字符串外形猜测究竟是 literal path 还是 pattern。变更使字面路径和模式路径有更可表达的区别，并要求相关 backend 保留解释一致性。

安全后果比语法更重要：若 deny path 被当作 pattern 而未匹配，程序可能意外获得读取能力；若字面路径误按 glob 扩展，又可能误杀正常文件。跨系统后端必须验证同一份 operator intent 是否产生相同的 enforcement 结果，尤其注意尚不存在的路径、symlink、特殊字符和文件系统差异。

### OpenShell 从 Sandbox 功能指标走向“多副本容量可运营”

同日深夜合入的 [OpenShell #3978](https://github.com/NVIDIA/OpenShell/commit/8b3cc3fdc067)（2026-10-05 15:38 UTC）新增每个 gateway replica 的 supervisor sessions、pending relay capacity、relay rejection、claim latency、outbound peer outcome/latency 等指标，采用受控 label 集和 Prometheus histogram，另提供可选 Helm HPA，并明确外部数据库、资源与 PostgreSQL connection sizing 等运行前提。这里的 HPA 是可选部署路径，不应解读为所有环境已具备自动扩缩容能力。

需要特别区分 *每副本容量* 与 *全集群容量*。一次请求被特定 replica 拒绝，不代表整个集群没有资源；反过来，实例总数增长也不代表后端数据库连接、supervisor session 和路由瓶颈自动消失。

## 新项目 / 版本

未发现足以创建独立 Project Entity 的全新正式发布。当天 [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk/commit/5a1867390b91) 在 legacy server 身份认证 API 增加 expectedResource 支持，属值得记录的资源受众边界改进，但不是 MCP wire protocol 新版发布。OpenAI Agents Python SDK 对 tracing opt-out 以及 resumed tool span 进行了局部修复，不能把 SDK 的修复等同于全行业规范改变。

## 论文 / 研究

本窗口重点增量来自维护者可审查的实现提交，没有核实到足以建立全新 Research Entity 的一手论文；不复述既有 Mid-Harness、AREX-2 或 SIFT 研究充数。

## 趋势判断

**趋势一：权限语言需要像编程语言一样接受 conformance 测试。** File policy、domain policy、HTTP request filter、credential scope 都有 parsing、normalization、pattern matching 与 conflict resolution；安全审查不能只看规则文本，而要看每个 backend 对同一规则的可执行解释。

**趋势二：Sandbox 的运营边界正下沉到 gateway replica。** 容量、connection ownership、admission 和路由需要联合可观测，不能只比较单次 sandbox boot latency。

## 工程启示

1. 为规则模型定义 `LiteralPath` 与 `GlobPattern` 的显式类型，不在 enforcement 时重新猜测。
2. 收集特殊字符、symlink、不存在路径、deny/allow 冲突及跨 OS backend 的 policy-conformance 测试集；解析不确定时 fail closed。
3. 分别监控 replica 的已连接 supervisor、待处理 relay、拒绝原因和路由延迟，避免 HPA 以 CPU 一项代理真实容量。
4. 将 PostgreSQL 最大连接、每副本会话预算、控制面滚动升级容量作为横向扩容的先决约束。
5. 对 MCP/OAuth 的 expectedResource 审核资源受众绑定，但不能仅由名称变化推导完整 credential isolation。

## Sources

- Anthropic sandbox-runtime — literal path marker merge（2026-10-04 17:39 UTC）：https://github.com/anthropics/sandbox-runtime/commit/80a235195af5
- NVIDIA OpenShell — gateway capacity metrics and optional HPA（2026-10-05 15:38 UTC）：https://github.com/NVIDIA/OpenShell/commit/8b3cc3fdc067
- MCP TypeScript SDK — expectedResource in legacy bearer auth：https://github.com/modelcontextprotocol/typescript-sdk/commit/5a1867390b91
- OpenAI Agents SDK — tracing opt-out：https://github.com/openai/openai-agents-python/commit/8c4aa0814fa1
- OpenAI Agents SDK — resumed approved tool traces：https://github.com/openai/openai-agents-python/commit/cf89d7ebdae8
