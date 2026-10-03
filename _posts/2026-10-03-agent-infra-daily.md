---
layout: post
title: "AI Agent 技术情报｜2026-10-03"
date: 2026-10-03 08:00:00 +0800
summary: "Agent 基础设施正在向可移植的运行环境、云端 sandbox 和低成本自我改进评估收敛。"
tags: [Runtime, Harness, Sandbox, Cloud Agent, Security, RSI]
---

过去约 24 小时没有出现 Claude Code、Codex、OpenHands 级别的重大 Harness 发布。今天更值得关注的是：**Agent 的运行环境正在被标准化成可移植 artifact；Cloud Sandbox 正从实验功能走向可复用基础设施；RSI 的关键瓶颈越来越集中在评估成本。**

## 今日最重要进展

### 1. Docker Sandbox Kit v3：把 Agent 的运行权限和环境打包成 OCI Artifact

Docker 在 9 月 24 日发布 Sandbox Kit Specification v3，并在本周文档中进一步明确其使用方式。Kit 可以描述 Agent workload、base image、工具、网络访问、credentials、setup commands 和 agent instructions，并以 OCI image 形式发布。

这意味着 Agent 的部署单位正在从：

```text
container image = code + dependencies
```

向：

```text
agent kit
= workload
+ runtime environment
+ tools
+ network policy
+ credential requirements
+ instructions
```

演进。

这对 Cloud Agent 很重要，因为它提供了一个潜在的“portable agent authority”层：不同 sandbox/runtime 可以解释同一个 Agent Definition，而不必把权限逻辑写死在具体 Harness 中。

成熟度：**Early Access / v3，可用于实验，不建议当前阶段直接绑定生产架构。**

### 2. Docker Cloud Sandboxes：本地 Coding Agent 开始获得可复用的云端执行环境

Docker Sandboxes 已支持以 `sbx --cloud` 在 Docker-managed infrastructure 上创建和恢复 Agent sandbox。官方文档当前列出 Claude Code、Codex、OpenCode 等 Agent，并支持命名 sandbox 的复用、重启与 detached 执行。

一个值得关注的设计是：云端 credentials 可以保存在 sandbox filesystem 之外的 secret store 中，而不是直接暴露给 Agent 工作目录。

更适合生产的 credential 路径应当是：

```text
Agent
  ↓
logical credential reference
  ↓
Credential Broker / Secret Store
  ↓
policy check
  ↓
External Service
```

而不是：

```text
export TOKEN=...
Agent reads env
```

成熟度：**Cloud support 仍属于新能力，但架构方向值得直接参考。**

## 值得关注的新项目/版本

### 3. DigitalOcean Agent Droplets：Agent Runtime 开始成为独立 Cloud SKU

DigitalOcean 在 10 月 1 日推出 Agent Droplets。其底层 Managed Agents public preview 已提供 managed runtime、16,000+ governed tools、Serverless Inference、persistent memory 和 storage；Agent Droplets 更像是在此基础上叠加统一套餐和成本控制。

这件事的技术创新有限，但产业信号非常明确：

```text
过去：
VM / Container / Function

正在增加：
Agent Runtime
```

未来 Agent 基础设施很可能出现新的计量单位：

```text
agent-hour
sandbox-hour
tool calls
model tokens
persistent workspace
```

成熟度：**Public Preview，适合 PoC。**

## 论文 / 研究

### 4. SIFT：Agent RSI 的昂贵部分不是“提出修改”，而是“验证修改”

论文 **Self Improvement via Fast Tree-search (SIFT)** 研究 coding agent 的 recursive self-improvement。核心观察是：候选 agent patch 很容易生成，但验证每个 patch 是否真的改进性能，需要重新跑 benchmark，成本高且耗时。

SIFT 引入：

```text
candidate patches
      ↓
LLM-as-a-judge pairwise comparison
      ↓
Bradley-Terry strength score
      ↓
rank-based tree search
      ↓
only promising candidates
      ↓
expensive downstream eval
```

这给 Agent RSI 一个很实际的工程启发：**真正需要被基础设施化的，不只是 self-modification，而是 eval scheduling。**

未来一个可生产的 Harness 自我优化系统，更可能长这样：

```text
Modification Generator
        ↓
Candidate Pool
        ↓
Cheap Evaluator
        ↓
Ranking
        ↓
Selective Expensive Eval
        ↓
Regression Suite
        ↓
Promotion
```

成熟度：**研究阶段，但 evaluation architecture 很容易迁移到生产 Agent 优化系统。**

## 趋势判断

过去几天的信息逐渐收敛出一个更完整的 Agent Infrastructure Stack：

```text
                 Agent Model
                      │
                      ▼
                Agent Harness
                      │
         ┌────────────┼────────────┐
       Memory      Planner      Subagents
                      │
                      ▼
               Durable Runtime
                      │
                      ▼
                Agent Artifact
            code + tools + policy
                      │
                      ▼
                 Policy Layer
            network / credential
                      │
                      ▼
               Sandbox Runtime
                      │
                      ▼
            Persistent Workspace
                      │
                      ▼
                 Cloud Compute
```

其中最值得观察的新层，是 **Agent Artifact / Agent Definition**。

如果这个方向成立，以后的 Agent 部署可能从：

```text
docker run agent
```

演进到类似：

```text
agent run coding-agent.kit
```

artifact 自己声明模型需求、MCP/tools、network capabilities、credential requirements、sandbox requirements 和资源限制，由底层 runtime 决定是否授权执行。

## 对工程实践的启示

对于面向大量用户的 Cloud Agent 平台，建议明确拆分：

```text
Agent Definition
├── Harness
├── Model policy
├── Tools / MCP
├── Network capabilities
├── Credential requirements
├── Sandbox requirements
└── Resource limits

Agent Instance
├── user_id
├── workspace_id
├── task_id
├── runtime state
├── execution journal
├── memory
└── artifacts
```

同时，Execution Trace 不应只用于 observability，而应成为：

```text
Execution Trace
├── observability
├── replay
├── incident analysis
├── eval dataset
├── skill mining
└── RSI candidate evaluation
```

今天最值得带回工程设计里的结论是：

> **Agent 的可移植定义、可恢复执行和可评估自我改进，正在从三个独立问题收敛成同一套基础设施。**

## Sources

- Docker — From Dockerfile to Kit: the Docker Sandboxes Kit Specification  
  https://www.docker.com/blog/docker-sandbox-kit-spec/
- Docker Docs — Kits  
  https://docs.docker.com/ai/sandboxes/customize/
- Docker Docs — Cloud Sandboxes  
  https://docs.docker.com/ai/sandboxes/cloud/usage/
- Docker Docs — Cloud Credentials  
  https://docs.docker.com/ai/sandboxes/cloud/credentials/
- DigitalOcean — Agent Droplets  
  https://investors.digitalocean.com/news/news-details/2026/DigitalOcean-Introduces-Agent-Droplets-Everything-an-AI-Agent-Needs-One-Simple-Monthly-Price/default.aspx
- SIFT — Self Improvement via Fast Tree-search  
  https://arxiv.org/abs/2609.19526
