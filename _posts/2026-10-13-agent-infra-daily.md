---
layout: post
title: "Agent Infra Daily · 2026-10-13"
date: 2026-10-13 08:23:00 +0800
summary: "OpenShell 日志恢复、Codex Host、ADK 生成续接、Open SWE checkpoint 与 Sandbox symlink deny。"
tags: [agent-infra, security, observability, durable-execution, sandbox]
---

## 今日最重要进展

**OpenShell loss-aware watchLogs。** [#3778](https://github.com/NVIDIA/OpenShell/commit/fe316067dc2503062235106b886c206e9d8ca079) 为 TypeScript SDK 增加日志与平台事件合流订阅。网络 Unavailable 自动退避重连，内部维护最大已交付 cursor；服务器 lag 作为 warning 而不推进游标，OutOfRange 终止而不静默从尾部开始。这种恢复只暴露缺口，并不保证日志永不丢失。

**Codex 网络代理的 Host 字段基数。** [#53506](https://github.com/openai/codex/commit/12cca49c81c8aa6a37a5cc4e39964ee3b70f9458) 在普通 HTTP 与 CONNECT 代理入口拒绝重复 Host，避免策略解析器与上游选择不同目标；相同值重复也返回 400。未证明 HTTP/2 authority、SNI 和 DNS 重绑定的所有路径都被覆盖。

**Open SWE 任务上下文持久化。** [#3988](https://github.com/langchain-ai/open-swe/commit/cd4f8143c4eb9b680a54580521f72202d34f1777) 把 Task Coordination 上下文从每次模型调用的临时注入移至 abefore_model 状态更新，以可见内容 hash 去重，进入 checkpoint 的可观察输入；摘要裁剪后的重新注入仍需测试。

**Google ADK Gemini 生成续接。** [提交](https://github.com/google/adk-python/commit/b3cbb4727727f5bc60e0161e850ce6c105cca952) 在 CONTINUATION finish_reason 下带 token 和已生成 parts 继续模型请求，聚合 usage；重复 token、未完成 function_call、256 次上限会终止。它不是任务级 durable execution，也不保证工具幂等。

**OpenShell 拒绝审批审计。** [#4281](https://github.com/NVIDIA/OpenShell/commit/3f12bdc63f4daf7752647bc0acb1d71c6f32ae0b) 在策略 chunk 持久拒绝后发 CONFIG:REJECTED，携带 actor、chunk_id、清洗后的原因与版本上下文。事件生成不等于日志存储的可靠送达。

**Anthropic sandbox-runtime symlink deny。** [#690](https://github.com/anthropics/sandbox-runtime/commit/b59244abe629036ac43e1c868d63b28e5c5646fa) 修复 Linux read-deny glob 中不可检查链接被真实路径/祖先目录折叠误消除的情况；路径原拼写与目标 realpath 必须分开表达。

## 新项目 / 版本

以既有核心项目的代码增量为主；本日没有足够一手证据支撑新增独立 Project Entity。重点关注 OpenShell TS SDK、ADK 生成协议与 Open SWE task context 的兼容性。

## 论文 / 研究

本窗口未核验到具有可复现方法、适合新增 Research Entity 的实质论文；不以旧论文或推测数字填充。

## 趋势判断

长期 Agent 的连续性不再只是进程存活：日志订阅需要明确永久缺口，任务上下文需要进入可恢复状态，模型续接不能冒充工具副作用 journal，Policy 决策必须保证解析唯一且拒绝可追踪。六项代码修复都只证明局部故障窗口，不能拼接为分布式 exactly-once 保证。

## 工程启示

- 区分 Execution Journal、Task Checkpoint、Model Continuation 与 Trace Cursor 的身份、版本、过期及重试语义；禁止共享同一“resume 成功”标志。
- 记录 tenant/sandbox/task/policy/decision/cursor 关联键，永久观测缺口要纳入 SLO，不能被自动重连隐藏。
- 在代理授权前校验 Host 基数，并独立测试 CONNECT authority、SNI、DNS/IP；文件 Policy 做 symlink 原路径与 realpath 的真实访问 conformance。
- 对任务上下文做 hash、来源版本和 checkpoint 关联；对工具副作用使用幂等键和 reconciliation。

## Sources

- https://github.com/NVIDIA/OpenShell/commit/fe316067dc2503062235106b886c206e9d8ca079
- https://github.com/openai/codex/commit/12cca49c81c8aa6a37a5cc4e39964ee3b70f9458
- https://github.com/langchain-ai/open-swe/commit/cd4f8143c4eb9b680a54580521f72202d34f1777
- https://github.com/google/adk-python/commit/b3cbb4727727f5bc60e0161e850ce6c105cca952
- https://github.com/NVIDIA/OpenShell/commit/3f12bdc63f4daf7752647bc0acb1d71c6f32ae0b
- https://github.com/anthropics/sandbox-runtime/commit/b59244abe629036ac43e1c868d63b28e5c5646fa
