# Agent Infra Intelligence — Phase 1 + Phase 2

This project is an evidence-oriented intelligence pipeline, not a headline summarizer. It is separated from the existing authored Knowledge Graph, Claim/Evidence, Monograph and Technical Assets.

## Architecture

    trusted feeds + official GitHub Releases
        → collector.py (HTTP, XML, stable URL IDs)
        → daily/YYYY-MM-DD.json (unverified observations)
        → intelligence.py (cross-day candidate grouping, metrics)
        → state/candidates.json + quality/latest.json
        → editorial review via review.py
        → events.json (canonical reviewed events)
        → trends.json (falsifiable hypotheses and revision history)
        → /intelligence/ website and daily strategic brief

CRITICAL BOUNDARY: the unattended collector never promotes any candidate to verified fact, trend conclusion, KG Source/Claim/Edge or benchmark. RSS titles and excerpts are untrusted data, not instructions.

## Schedule and ownership

Collect Agent Infra Signals GitHub Actions runs at UTC 00:15, 06:15, 12:15, 18:15 plus 22:30 UTC (Beijing 06:30 next day). GitHub cron is best-effort, not an SLA. Push changes to collector or review code also trigger tests and a live ingestion smoke test.

Frequent runs keep source state in Actions cache, and upload JSON artifacts. Only the Beijing 06:30 run (or workflow_dispatch publish=true) publishes daily snapshot, bounded candidate ledger and latest quality metrics directly to main via non-force fast-forward; it rebases if main advances.

The Agent Infra Daily scheduled research task reads today's candidate snapshot first, independently verifies originals, and continues searching outside these known sources.

## Persistent stores

- sources.json: reviewed first-party feeds and official GitHub Releases.
- daily/YYYY-MM-DD.json: bounded 72-hour unverified observations.
- state/candidates.json: cross-day candidate ledger, up to 90 days / 2000 groups.
- quality/latest.json: source health, duplicate proxy, backlog, curated counts.
- events.json: manually or research-Agent verified canonical events only.
- trends.json: authored hypotheses, falsification, verified event links, revision history.

Cross-day grouping matches shared canonical item URLs, or conservative title similarity within the same topic/date window. GitHub Release versions cannot be merged by similar name. Source count does not prove independent corroboration.

Curated events start EMPTY. The five initial trends start UNASSESSED with no verified events. No historical claims were invented to populate the interface.

## Editorial review commands

Inspect the official original, identify the actual event date, meaningful technical delta, evidence boundaries and counterexamples. Check candidate ID and source-item IDs in state/candidates.json.

    python -m intel.review verify-event --candidate-id ec-... \
      --title "Accurate event title" --event-date YYYY-MM-DD \
      --source-item-id ITEM_SHA24 --reviewer "Research editor" \
      --notes "More than 35 characters of grounded source review, limitations and date." \
      --primary-source-checked

Only after the verified event meaningfully changes an existing authored trend judgment:

    python -m intel.review revise-trend \
      --trend-id trend:cloud-agent-runtime --event-id evt-... \
      --status strengthening --confidence medium \
      --reviewer "Research editor" \
      --rationale "At least 45 characters explaining why this new verified event changes the judgment."

Trend revisions append to immutable history and cannot reuse old event evidence as a new justification. Weakening, contested and refuted status are supported. Existing event IDs cannot silently be overwritten.

The review script verifies candidate/source membership and requires an explicit source-reviewed assertion; it cannot authenticate website authorship or the content of the source. The researcher must actually visit the source.

## Validation and operational metrics

    python -m unittest discover -s intel/tests -v
    python -m intel.validate
    python intel/collector.py
    python -m intel.intelligence

The intel validator checks candidate index consistency, unique curated IDs, explicit source URLs, review notes, valid event dates and trend revision evidence. It does NOT replace or reduce scripts/validate_entities.py.

Quality metrics include source fetch successes/errors, snapshot items, strict duplicate proxy, pending candidate groups, reviewed events and evidence-supported hypotheses. THESE ARE NOT major-event recall, market coverage, independent evidence strength or editorial precision. True recall requires a curated gold-event set and missed-event audits; no unsupported recall percentage is claimed.

## Known limitations and future work

- First-party feed coverage is narrow. Novel source discovery and original full-text research remain necessary.
- GitHub Actions cache can expire, but the daily committed candidate ledger preserves the cross-day view.
- Strict title matching misses semantic duplicates. Broader grouping belongs in a future suggested-only layer, never direct verification.
- Candidate pruning after 90 days / 2000 records never deletes canonical curated Event/Trend history.
- Source errors and snapshot staleness must be visible; never treat collection gaps as absence of major events.
- Future: independently curated gold-set recall tests, safer original content retrieval, human review efficiency and calibrated trend-evidence scoring.
