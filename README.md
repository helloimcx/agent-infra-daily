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


## Analysis layer

- `/analysis/` — analysis hub
- `/compare/` — evidence-linked capability coverage comparison
- `/stack/` — analytical architecture stack projection
- `_data/kg/architecture.json` — curated architecture-layer projection; this is analysis, not factual ontology

Comparison and architecture views derive from the same knowledge graph and preserve the distinction between fact-backed and analytical relationships.


## Entity pages

Every knowledge-graph node has a first-party detail page under `/entities/<type>--<slug>/`.

Entity pages contain:
- detailed overview and why-it-matters text
- theme and maturity metadata
- local relationship graph
- fact vs analysis relationships
- architecture-layer projection
- evolution anchors
- primary evidence
- related daily briefs

External URLs are treated as evidence sources, not as the node's canonical page.


## Entity schema v2

Core entities use type-specific fields from `_data/kg/entity_schema.json`; entity pages render only fields that exist and keep evidence-backed facts separate from analysis.


## Authored entity content guardrail

Entity prose is first-party knowledge content, not a rendering of graph metadata.

- Every node must set `content_mode: authored` and `content_version: v7`.
- Every node must have a unique, explicitly written `intro` and `why_it_matters`.
- Core types must satisfy their type-specific schema in `_data/kg/entity_schema.json`.
- The legacy generated `overview` field is forbidden.
- Graph relations may be displayed and used for fact checking, but they are not prose templates.
- `.github/workflows/validate-knowledge.yml` runs `scripts/validate_entities.py` and blocks missing/thin/templated entity content.


## Claim evidence model

V7 adds `_data/kg/claims.json`. Claims are authored statements attached to one entity and explicitly marked as `fact`, `analysis`, or `hypothesis`, with confidence and one or more Source nodes as evidence. Entity pages render these claims near the technical article instead of forcing readers to infer provenance from a source list at the bottom.


## Technical monographs

Every entity now has a standalone authored research entry in `_data/kg/monographs.json`.

The monograph is deliberately separate from `nodes.json`:
- `nodes.json` models identity, metadata and graph-facing structured knowledge.
- `monographs.json` stores the long-form technical research: mechanisms, state/lifecycle, failure semantics, security boundaries, tradeoffs, evidence scope, operations and open questions.
- The text must be written for the individual entity. It must never be produced by concatenating graph fields.

CI enforces type-specific minimum section counts and content depth. Core Project/Capability/Research entries require substantially deeper monographs than supporting Event/Source nodes.
