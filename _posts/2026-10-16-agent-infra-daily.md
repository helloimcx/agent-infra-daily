---
layout: post
title: "Agent Infra Daily · 2026-10-16"
date: 2026-10-16 08:03:00 +0800
summary: "LangGraph 恢复任务身份、OpenShell DNS 授权权威、Codex 远端凭据轮换和 Open SWE 命令结果不确定性。"
tags: [agent-infra, durable-execution, sandbox, security, credential-isolation]
---

## 今日最重要进展

**LangGraph #9315（北京时间 10 月 16 日 03:51）** 修复普通 checkpoint resume 时已完成并行/子图任务被重新执行的问题。#9314（03:26）进一步限制 exit durability 只重新保存本轮实际产生的 pending writes。恢复身份与历史回放身份必须区分。

**OpenShell #4602（10 月 16 日 01:56）** 将名称授权绑定到可信 Supervisor DNS；Sandbox 可控 /etc/hosts 仅在独立 IP/CIDR pin 下参与解析，避免域名许可被工作负载重定向到任意目标 IP。

**Codex #54434（10 月 16 日 06:32）** 新增远程 exec-server 的 --executor-credential-stdin，支持初始凭据等待、轮换与父进程生命周期绑定，并隔离账号级身份和可能含密钥的 telemetry exporter。相关 #54346 完善 scoped registration 授权。

**Open SWE #4120（10 月 16 日 00:58）** Sandbox reconnect 找不到命令结果时报告 UNKNOWN OUTCOME，不自动 fallback 重放可能已经产生副作用的 shell 命令。结果丢失不等于命令没有执行。

## 新项目 / 版本

Open SWE #4110 为直接 Agent Server API 增加后端写权限和用户线程所有权读取过滤。Browser Use 0.13.12 引入基于 Actor 的 OpenAI Browser Tool 驱动和 Cloud 浏览器生命周期管理。Google ADK 修复 A2A task 转事件时丢失 artifact；OpenHands 修复共享 TMUX_TMPDIR 下启动清理误杀兄弟实例会话。

## 论文 / 研究

本窗口没有核验到足以新增独立 Research Entity 的高质量新论文，不添加未经证实的 benchmark 数字。

## 趋势判断

Agent Runtime 的正确性正分解为 Task Replay Identity、Command Outcome 与 Authorization Authority。它们分别约束完成任务能否重跑、结果未知时是否重试，以及恢复后执行器实际被允许访问的目标。

## 工程启示

持久化 TaskID、CheckpointID、ToolCallID、CommandID、CredentialEpoch 和 WorkerLease；对 resume、time travel、UNKNOWN OUTCOME 分别故障注入。网络策略区分名称授权和 IP 授权；凭据轮换覆盖遥测、重连与父进程退出。监控增加重复执行计数、未知结果比例、DNS policy divergence 和 credential rotation 失败率。

## Sources

- LangGraph resume: https://github.com/langchain-ai/langgraph/commit/b0482d0627ec8fdf7c91fba7ffd17403583c59d0
- LangGraph pending writes: https://github.com/langchain-ai/langgraph/commit/889a5ff16f8325113093d517dffd5471a943c760
- OpenShell DNS: https://github.com/NVIDIA/OpenShell/commit/c5519ea8ba5c2f519f25ff7897ffc1fe62536c22
- Codex rotating credentials: https://github.com/openai/codex/commit/16e578dd1ddaf4f5db9cd1f3dbfea0958fd74339
- Codex scoped registration: https://github.com/openai/codex/commit/0003732489a514748e61a0f76a652ac992a5f4f5
- Open SWE unknown outcome: https://github.com/langchain-ai/open-swe/commit/e06c33b7cb0cb338eab836f33f7bf3491cb4fafc
- Open SWE API auth: https://github.com/langchain-ai/open-swe/commit/3df68ff6e0155cbac220201d2a5e6c4c8dba06f7
- Browser Use integration: https://github.com/browser-use/browser-use/commit/a93d9b977322394d5b924542d906bce4871bfb15
- Google ADK A2A: https://github.com/google/adk-python/commit/e3e6581354
- OpenHands tmux: https://github.com/OpenHands/software-agent-sdk/commit/f0206428306db687ac9c8d833ece4fb82b015eba
