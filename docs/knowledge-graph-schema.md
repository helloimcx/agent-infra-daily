# Agent Infra Knowledge Graph Schema

Daily briefs are evidence streams; the graph is the long-lived knowledge model.

## Files

- `_data/kg/ontology.json`: node and edge taxonomy.
- `_data/kg/topics.json`: top-level themes.
- `_data/kg/nodes.json`: canonical entities.
- `_data/kg/edges.json`: typed relationships with provenance and time.
- `_data/kg/aliases.json`: entity-resolution aliases.
- `_data/kg/deltas/YYYY-MM-DD.json`: exact graph changes from each daily run.
- `knowledge.json`: public machine-readable endpoint.
- `graph/`: interactive graph explorer.

## Canonical IDs

Use stable semantic IDs such as `theme:runtime`, `cap:durable-execution`, `project:restate`, `research:mid-harness`, and `trend:harness-rsi`.

## Facts vs analysis

Every edge has a `kind`: `taxonomy`, `fact`, `analysis`, or `hypothesis`. Factual edges should normally contain one or more Source node IDs in `evidence`.

## Time

Nodes and edges track at least `first_seen` and `last_verified`. Events use the actual event/publication date when known.

## Daily update algorithm

1. Read existing nodes, edges and aliases.
2. Extract entities and relations from evidence-backed research.
3. Resolve aliases before creating entities.
4. Update `last_verified` for re-confirmed facts instead of duplicating edges.
5. Add Source and Event nodes for meaningful new evidence.
6. Keep interpretations as `analysis` or `hypothesis`.
7. Write the daily graph delta.
8. Write the daily brief.
9. Commit both together when possible.

The system should become less repetitive over time: research should focus on **knowledge delta**, not repeatedly restating existing nodes.