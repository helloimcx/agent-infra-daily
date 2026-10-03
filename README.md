# Agent Infra Daily

Daily intelligence on AI Agent infrastructure, runtime, harnesses, sandboxes, cloud agents, memory, observability, security and agent RSI.

## Content model

Each daily report is a Jekyll post under `_posts/`:

```text
_posts/YYYY-MM-DD-agent-infra-daily.md
```

Required front matter:

```yaml
---
layout: post
title: "AI Agent 技术情报｜YYYY-MM-DD"
date: YYYY-MM-DD 08:00:00 +0800
summary: "一句话概括当天最重要的技术变化。"
tags: [Runtime, Harness, Sandbox, Cloud Agent, RSI]
---
```

The report body should use this order:

1. 今日最重要进展
2. 值得关注的新项目/版本
3. 论文/研究
4. 趋势判断
5. 对工程实践的启示
6. Sources

## GitHub Pages

This repository is designed for GitHub Pages + Jekyll with no custom build step.

Enable **Settings → Pages → Deploy from a branch → `main` / `(root)`**.

Site URL:

https://helloimcx.github.io/agent-infra-daily/


## Knowledge graph

The site maintains a living knowledge graph:

- `_data/kg/nodes.json` — canonical entities
- `_data/kg/edges.json` — typed, evidence-linked relationships
- `_data/kg/deltas/` — daily graph changes
- `/graph/` — interactive Cytoscape.js explorer
- `/topics/` — topic-oriented browse view
- `/knowledge.json` — machine-readable endpoint

See `docs/knowledge-graph-schema.md` for modeling rules.
