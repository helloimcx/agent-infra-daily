---
layout: post
title: "Agent Infra Daily｜2026-11-14：会话工作台与状态恢复的真实边界"
date: 2026-11-14 08:00:00 +0800
summary: "Codex 0.169.0 正式版增强多会话工作台、Provider 管理与中断清理；LangGraph4j 修复 checkpoint 重复归约。重点区分交互恢复、执行状态恢复与外部副作用一致性。"
tags: [agent-infrastructure, codex, durable-execution, sandbox, cloud-agent]
---

## 今日核心判断

**Coding Agent 的会话工作台正在成熟，但 UI 中可重新打开会话、计划交接成功与业务任务可安全恢复是不同层次。** 11 月 13 日两项正式发布为这一判断提供了新证据：Codex 0.169.0 改善会话管理与中断语义，LangGraph4j 1.8.28 修复 checkpoint 更新时的状态归约错误。它们都没有单独证明端到端 Exactly-once 或百万用户级高可用。

## 重大进展与证据边界

### 1. Codex 0.169.0 正式版：多会话、Provider 与执行中断边界

OpenAI 官方 GitHub Release 于 2026-11-13 08:37 UTC（北京时间 16:37）发布，标记为非 prerelease。可选终端工作区支持多个 side-chat 标签，并能在重启后重新打开本地保存的 side chats；命令中心支持按名称、提示预览、工作目录搜索旧任务；终端可配置自定义 Provider，部分网关支持 device-code 登录。修复项包括：在不可信目录下，即使使用 `--sandbox workspace-write`，`codex exec` 仍保持项目配置和 MCP servers 禁用；清理被中断的 turn，避免延迟 abort/文件审批取消误伤后续 turn；“clear context and implement” 交接失败时保留当前会话。

**边界：** Release 证明客户端与安全控制改进，不代表不同 Provider 之间可以无损迁移 checkpoint、授权或外部操作回执；重开本地 side-chat 不等于恢复 Sandbox 进程。未见该版本官方发布的百万用户吞吐或恢复成功率 Benchmark。

### 2. LangGraph4j 1.8.28：Checkpoint 状态归约必须有精确语义

官方 Release 于 2026-11-13 09:04 UTC（北京时间 17:04）发布，非 prerelease。修复 `nextNodeId` 已解析的完整状态再次与 checkpoint 合并造成 channel 值重复归约的问题，并覆盖条件边删除、重置、显式 checkpoint 更新及单图恢复等测试。

**边界：** 这是具体状态正确性修复，而非整个 LangGraph 生态或跨服务 Exactly-once 保证。Java 实现的修复不能直接外推到其他语言实现。

### 3. OpenShell v0.1.8：较早版本中的安全与资源成本信号

11 月 10 日发布的正式版（不是今日新品）修复了反复创建/删除 Sandbox 导致 Gateway 内存增长的问题，并取消每 Sandbox 约 3.4 MiB 的预分配流缓冲区；同时调整凭证位置声明、OCSF 字段和文件系统符号链接策略。此处只作为最近一周的对比证据，官方变更量不能当作生产节省成本的实测数据。

## 架构路线与 Tradeoff

- **Codex/交互工作台：** 提升会话发现、交接和 Provider 可配置性；代价是状态来源更多，必须定义会话元数据、工作区版本与权限状态的归属。
- **LangGraph/持久工作流：** checkpoint 与图状态更新语义更明确；代价是版本迁移、重放确定性和外部副作用仍需独立设计。
- **OpenShell/隔离执行：** 沙盒资源效率、审计和最小权限改进；代价是共享故障域、凭证迁移及升级兼容性需要演练。

## 标准与研究

过去约 24 小时的官方来源抽查未确认足以写成 P0 的新正式 Agent 标准。MCP 连接协议、工具授权、Checkpoint 及执行账本仍不能互相替代；避免将单一 Release 的功能扩展解释为行业标准落地。

## 7/30 天趋势雷达

- **加强（7天，工程信号）：** 多会话工作台与可配置 Provider；恢复/取消的状态正确性问题继续获得修复证据。
- **加强（30天，低置信）：** 工具 Registry 与执行授权分离。仓库已核验的 AWS Registry 参考架构支持该方向，但仅有单厂商案例。
- **待证实：** 独立 Durable Runtime 控制面、跨 Sandbox 可移植 Workspace 与低成本共享 Supervisor 的生产规模收益。
- **减弱/推翻：** 本期无足够独立反证；不凭未采集到消息判断趋势失败。

## 百万用户 Cloud Agent：本周可执行建议

建立 `SessionRecord → WorkspaceVersion → TaskCheckpoint → AuthorizationFence → ExecutionLedger` 五层契约。SessionRecord 保存可搜索的交互索引；WorkspaceVersion 记录不可变代码/文件快照；TaskCheckpoint 以 schema version 与 CAS 防止旧状态覆盖；AuthorizationFence 在恢复与每次有副作用工具调用前重新核验 principal、授权版本与撤权；ExecutionLedger 以 operation ID、幂等键、请求摘要和回执实现重试对账。

优先开展四组故障注入：① clear-context 交接失败；② checkpoint 重放导致重复 reducer；③ 中断/取消延迟到达下一轮；④ Sandbox 已执行外部写入但回执丢失。分别统计状态不一致率、重复外部操作次数、撤权后越权次数、恢复 p95/p99 与单位成功任务成本。所有指标均为待测，不编造结果。

## 情报质量与证据局限

截至本次读取，`intel/daily/2026-11-14.json` 尚不存在。最近可用 11 月 13 日快照显示 19 个信源中 18 个抓取成功，`deepmind-blog` 失败；当期 88 条候选、跨日未核验积压 609 条。独立 Gold 样本为 0，重要事件召回率无法计算。候选、RSS 时间及 Sitemap lastmod 均不能代替原文核验。仓库长期趋势记录只有 2 个已人工核验事件，不能据此声称行业广泛采用。

长期预测仍保持原有注册条件与概率：2027-03-31 前不提前判 YES/NO。本期不变更 KG 长期实体；对应 Delta 四组空数组。

## 官方 Sources

1. [OpenAI Codex 0.169.0 正式 Release](https://github.com/openai/codex/releases/tag/rust-v0.169.0)，2026-11-13 08:37 UTC。
2. [LangGraph4j 1.8.28 正式 Release](https://github.com/langgraph4j/langgraph4j/releases/tag/v1.8.28)，2026-11-13 09:04 UTC。
3. [NVIDIA OpenShell v0.1.8 正式 Release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.8)，2026-11-10 18:14 UTC。
4. [AWS Agent Registry 官方技术文章](https://aws.amazon.com/blogs/machine-learning/discover-tools-at-runtime-with-aws-agent-registry)，历史基线，非今日发布。
