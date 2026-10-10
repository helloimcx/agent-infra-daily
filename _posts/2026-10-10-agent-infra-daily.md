---
layout: post
title: "Agent Infra Daily · 2026-10-10"
date: 2026-10-10 08:37:00 +0800
summary: "LangGraph DeltaChannel 因果回放、OpenShell/Codex 凭据别名安全、Open SWE Remote MCP 与 OpenHands 风险审计。"
tags: [agent-infra, durable-execution, credential-isolation, mcp, security, observability]
---

## 今日最重要进展

**1. LangGraph 修复 DeltaChannel checkpoint 因果顺序（10 月 9 日 20:48 北京时间）。** [#9235](https://github.com/langchain-ai/langgraph/commit/cba111d8d600a027324eba1120a22e82b7f07432) 让后台 checkpoint 保存等待本次增量写入及前序 checkpoint 成功，防止写入失败后发布不可完整回放的后继状态。同期 [#9260](https://github.com/langchain-ai/langgraph/commit/12aeb0fddb5e835a5745a10a72358c2de37a66a6) 约束运行输入的 checkpoint 归属，[#9263](https://github.com/langchain-ai/langgraph/commit/d05236f8050c28d38449f81e25382d5991a29223) 修复 Overwrite 后的快照重放。这些修复涉及因果一致性，不等于跨后端 exactly-once 保证。

**2. OpenShell 保留 JWT-shaped 凭据别名的签发身份（10 月 10 日 05:22）。** [#4390](https://github.com/NVIDIA/OpenShell/commit/0ccc6b9a053fdaf47700e91c1b8ed858f2afed4f) 将完整 issued placeholder suffix 放入 JWT signature 段，Claims 仅用于客户端元数据；endpoint、expiry、authorization epoch 继续约束注入。测试覆盖轮换、撤权、过期与畸形 alias。

**3. Codex 修复 brokered credential alias 绕过 MITM hooks（10 月 10 日 02:04）。** [#52661](https://github.com/openai/codex/commit/65b82cdf96f9d305494bc8c6c8d2404d37709030) 调整 credential broker、destination、proxy 与 MITM 检查并补充网络审批测试。凭据代理需要同时验证 issued identity 与实际请求目标。

**4. Open SWE 提供外部 Agent 的远程 MCP 私有线程工具（10 月 10 日 06:04）。** [#3855](https://github.com/langchain-ai/open-swe/commit/6a5071bcefbb851dbb563388334ac84ddbbffe70) 使用后端 `/oswe/mcp`；`upload_session` 创建 thread 和一次性 code，本地 CLI 再上传 JSONL transcript。Remote MCP 不代表 thread ownership 和上传流程无状态。

**5. OpenHands SDK 增加逐批次安全分析事件（10 月 10 日 00:24）。** [#5182](https://github.com/OpenHands/software-agent-sdk/commit/9e76fe72b43f7be65b48a243486c2e30b5104a22) 输出脱敏 `SecurityAnalysisEvent`，记录 analyzer verdict 以支持审计回放；SDK 风险事件不等于 out-of-band 强制授权。

## 新项目 / 版本

- [OpenHands software-agent-sdk v1.54.0](https://github.com/OpenHands/software-agent-sdk/commit/1d471742ea7b) 发布，agent-server 同期 [拒绝空白与 redacted secret](https://github.com/OpenHands/software-agent-sdk/commit/c1c8c1c27824)。
- [Codex #52723](https://github.com/openai/codex/commit/2dc0791c7d2cb4decda6b8ebd8b54d38d7411f64) 新增 opt-in gRPC over stdio 的 code-mode host，单 HTTP/2 连接关闭后停止 host，并非默认切换。
- [E2B #1963](https://github.com/e2b-dev/E2B/commit/0ad4ec1e02dab2777d2ad53ecd4a8178711f46d9) 使受支持域名的 Jupyter 请求通过统一 sandbox endpoint；其他域名与浏览器仍保留 per-port 路径。
- [Google ADK](https://github.com/google/adk-python/commit/15486dbb2ac26284f4384857acc0d4002f4e4fc4) 给 ComputerUseToolset/EnvironmentToolset lazy initialization 加并发保护；锁按 event loop 划分，跨线程共享实例仍有边界。

## 论文 / 研究

未发现近 24 小时内能够同时核验一手技术细节与发表日期、并构成明确机制增量的 Agent Infra 新论文；因此不新增 Research Entity 或未经复核的 benchmark 数字。

## 趋势判断

Durable Execution 的质量标准从“checkpoint 存在”转向“中断、失败、分叉后因果一致地回放”。Credential Broker 的安全标准从“Agent 看不到 secret”转向“签发身份、目标请求、撤权语义均可验证”。Remote MCP 接口与长期 thread/worker 的状态生命周期进一步分离；安全分析事件提供可回放证据，但不能代替强制执行点。

## 工程启示

1. Cloud Agent journal/step/checkpoint 显式保存 write-set identity、parent 与提交栅栏；测试失败写入、fork、Overwrite 和 worker 重启后的 replay equivalence。
2. Credential broker 绑定 issuer、workload、epoch、destination、expiry；注入前后同一网络策略检查，旧 token、JWT 包装、代理重试和重定向进入安全回归集。
3. 将 SecurityAnalysisEvent、PolicyDecision、ToolCall、Approval 关联到统一 correlation ID；审计脱敏，独立 Gateway/Sandbox 负责强制授权。
4. Remote MCP 上传码须测试 owner、单次消费、partial upload 与重试幂等；HTTP 无状态不代表任务无状态。
5. Code-mode host 与 Computer Use toolset 应测试取消、关闭和多 event loop 竞争，防止初始化竞态与资源泄漏。

## Sources

- https://github.com/langchain-ai/langgraph/commit/cba111d8d600a027324eba1120a22e82b7f07432
- https://github.com/langchain-ai/langgraph/commit/12aeb0fddb5e835a5745a10a72358c2de37a66a6
- https://github.com/langchain-ai/langgraph/commit/d05236f8050c28d38449f81e25382d5991a29223
- https://github.com/NVIDIA/OpenShell/commit/0ccc6b9a053fdaf47700e91c1b8ed858f2afed4f
- https://github.com/openai/codex/commit/65b82cdf96f9d305494bc8c6c8d2404d37709030
- https://github.com/langchain-ai/open-swe/commit/6a5071bcefbb851dbb563388334ac84ddbbffe70
- https://github.com/OpenHands/software-agent-sdk/commit/9e76fe72b43f7be65b48a243486c2e30b5104a22
- https://github.com/OpenHands/software-agent-sdk/commit/1d471742ea7b
- https://github.com/openai/codex/commit/2dc0791c7d2cb4decda6b8ebd8b54d38d7411f64
- https://github.com/e2b-dev/E2B/commit/0ad4ec1e02dab2777d2ad53ecd4a8178711f46d9
- https://github.com/google/adk-python/commit/15486dbb2ac26284f4384857acc0d4002f4e4fc4
