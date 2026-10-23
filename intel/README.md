# Agent Infra Intelligence — Phase 1 + Phase 2 + Phase 3

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
    python -m intel.collector
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

## Phase 3 — auditable significant-event discovery

The curated `intel/evaluation/gold_events.json` contains first-party
events explicitly reviewed by the research agent. Each record identifies the
Beijing event date, upstream primary URL, expected collector source ID,
importance, review time and substantive evidence limitations. This is a
SMALL EDITORIAL SAMPLE, not a representative industry census.

On every real collection run, `python -m intel.evaluation` compares these
gold events to the unverified candidate snapshot via exact canonical official
URL matching, not semantic title matching or vendor marketing summary.

The output `intel/quality/coverage.json` has three distinct outcomes:

- captured: an eligible gold event's original URL was seen in raw candidates;
- source_not_monitored: the gold event's originating official source does not
  exist in the collector configuration (discovery coverage gap);
- in_scope_not_observed: an eligible event from an enabled official source was
  not observed (feed/API freshness, item filtering or fetch failure).

The output contains capture fraction for the deliberately hand-picked sample
and separately for only in-scope events, with an explicit caveat that these
numbers are not population recall. A gold item's Beijing event date may be
day-level only. The evaluator uses deliberately broad day eligibility and
does NOT claim exact hour-level latency.

First reviewed records:

- Anthropic Claude Duet, 2026-10-21: official announcement verified, but
  Anthropic product announcements are not yet in the collector. This is a
  real source coverage gap, not a falsely reported within-feed false negative.
- AWS Agent Registry runtime discovery, 2026-10-21 Beijing (Oct 20 UTC source):
  the official machine-learning feed already contains this article.
- OpenHands software-agent-sdk v1.57.0, 2026-10-21: official GitHub Release
  API observed this version.

Two real candidate records from a successful Actions artifact are explicitly
bootstrapped into state; they are NOT an assertion that all 54 initial items
have already been committed. Future daily ingestion merges the full snapshot.

Canonical `events.json` now contains two primary-source reviewed events,
and one long-term tool-governance hypothesis received its first low-confidence,
evidence-linked revision. The other hypotheses remain unassessed. The
collector/evaluator may NOT modify those editorial records.

To validate:
    python -m unittest discover -s intel/tests -v
    python -m intel.validate
    python -m intel.evaluation

The Gold audit must grow by independent human/research-agent reviewed events
across different vendors, not by duplicating whatever the collector happens
to see. Regularly sample missed major external news to avoid survivorship bias.

## Phase 4 — official source discovery and coverage expansion

The collector now reads additional official first-party RSS feeds:
OpenAI News, Google DeepMind, Google AI Blog and Mistral News.
Each URL must be live-tested through GitHub Actions; configuration is not
proof that a feed is healthy or complete.

Anthropic and Claude have no consistently documented official RSS endpoint.
Instead the pipeline reads a narrowly scoped official XML sitemap from
anthropic.com and claude.com when available. Only recently modified HTTPS
article URLs on the configured host and approved path prefixes are admitted.
Nested sitemap traversal is bounded and same-host only; DTD and entity
declarations are rejected.

**Sitemap lastmod is not an article publication timestamp.** A sitemap URL is
a *discovery hint*, and items have published_at=null, date_basis=
site_lastmod_not_publication. Actual event times and product maturity must
be verified from the official original before any authored Event/Trend/Claim.

Failure semantics: partial nested sitemap failures are reported as warnings,
not hidden; unavailable sitemaps are errors. All listed source health and
candidate totals must be reviewed after the real workflow run. The sample
coverage audit distinguishes an unmonitored source from an official source
that was configured but did not yield the expected original URL.

Do not automatically add discovered URL titles to the canonical KG; maintain
the evidence review contract described in the earlier phases.

### Phase 4 source smoke-test findings

A real GitHub Actions run of the initial expanded source list collected 92
candidates from 19 sources. The OpenAI, DeepMind, Google AI and Mistral feeds
returned parseable entries, and the Anthropic official sitemap returned 112
recently modified URL hints. However the Claude product sitemap returned ZERO.
A successful HTTP request does not imply meaningful event coverage.

The collector therefore also scans the first-party Claude product-announcements
HTML listing, extracting only approved same-host /resources/articles/ links.
These are discovery candidates only: published_at stays null, with
date_basis=official_listing_no_verified_publication_time. No HTML-based
inferred time may become the actual release date without opening the original.

A zero-result official sitemap/listing is now exposed as a source warning,
and a partial source health status, even if HTTP returned 200.

The gold evaluation now includes configured official sitemaps and listing IDs
when classifying source_not_monitored vs in_scope_not_observed. This fixes a
previous audit misclassification where a monitored sitemap was mistakenly
not included in the configured-source set.

### Source efficacy and rolling-window audit correction

After live testing, the Claude product sitemap source (zero relevant URLs)
was removed; first-party Claude product-announcements HTML now covers the
Duet official original. HTML listing records lack verified publication
timestamps and are never promoted automatically.

A gold item previously observed in the persistent candidate ledger is now
marked `captured_in_history` if it no longer appears in today's bounded feed
snapshot. This prevents confusing normal RSS window expiry and release
pagination with a never-detected event. The quality report separates
snapshot_captured_count and historical_captured_count. Every item still
requires editorial review before being called a verified technology event.


## Phase 5 — transparent review ordering and independent weekly checks

The new `intel/triage.py` produces `intel/triage/latest.json` from the most
recent snapshot, persistent candidate IDs and curated verified events.
It DOES NOT classify true significance or make claims. Its deterministic
reading order uses configured editorial source priority, official Release/Feed
provenance and claimed timestamps only. Official listing/sitemap discovery
has no verified publication time and earns no recency bonus. Curated verified
Events are omitted from the queue. Explanations and per-source/topic caps
are always recorded. Score is not a probability or confidence estimate.

The daily GitHub Actions job attaches this queue to the workflow artifact;
only the Beijing 06:30 publication commits it to main. The daily research
task should use the queue as a reading suggestion, not a source of truth
or replacement for direct independent discovery.

The `Weekly Agent Infra Intelligence Audit` GitHub Actions workflow runs
Sundays at 09:00 Beijing, following the daily snapshot. It validates
everything and writes `intel/weekly/YYYY-Www.json` directly to main if
the weekly worksheet does not exist. Existing weekly worksheet editorial
annotations are never overwritten. Manual dispatch defaults to dry run.

A weekly worksheet records source freshness, candidate backlog, sampled
gold coverage, verified events reviewed in the past seven days, trend
revision evidence, stale hypotheses, and four independent review tasks:
model-provider launches, cloud runtime/security, research/standards, and
counterexample/unknown-source discovery.

IMPORTANT: generating this worksheet does NOT mean independent research
was performed. Each task initially has status
`pending_independent_primary_source_search`. The final editorial signoff
remains `pending` until a researcher reviews original sources beyond
the queue, records misses, and challenges prior trend judgments.
No spurious prediction-accuracy metric is calculated; true calibration
requires registered forecasts and independent outcome checks.

Run with stdlib Python 3.12:

    python -m intel.triage
    python -m intel.weekly_quality --output intel/output/weekly-preview.json
    python -m unittest discover -s intel/tests -v
    python -m intel.validate

These quality modules do not modify the existing curated KG/Claims/Monographs.


## Phase 6 — pre-registered and falsifiable architecture forecasts

The long-term trend labels strengthening/weakening are NOT calibrated
predictions. Two editorially owned data stores now exist:

- `intel/forecasts.json` freezes forecast ID, linked Trend, explicit
  YES/NO criteria, time horizon, subjective P(YES), verified-event baseline,
  source limitations, reviewer and architecture decision impact.
- `intel/forecast_outcomes.json` stores separately reviewed YES, NO, or
  VOID judgments, evidence URLs and applicable verified canonical events.

The collector, RSS triage and unattended weekly audit must NEVER make or
resolve predictions. Forecast parameters are frozen at registration. An
overdue prediction simply needs review; it is never automatically wrong.
YES needs a new first-party verified Event inside the registered interval.
NO requires reaching the deadline and independent examination of at least
two official primary-source URLs. VOID must document an invalid criterion;
it is never counted as a correct prediction. The registration/outcome CLI
blocks duplicate IDs and overwriting existing outcome reviews.

To register a researched forecast (replace placeholders with substantive
text and actual verified IDs):

    python -m intel.forecasts register --forecast-id fc-... \
      --trend-id trend:tool-governance --question "..." \
      --yes-condition "..." --no-condition "..." \
      --target-date YYYY-MM-DD --probability-yes 0.55 \
      --baseline-event-id evt-... --baseline-note "..." \
      --decision-impact "..." --reviewer "Research editor"

To record an editorial resolution after reading original source material:

    python -m intel.forecasts resolve --forecast-id fc-... \
      --outcome yes --evidence-event-id evt-... \
      --reviewed-url https://official.example/original \
      --rationale "..." --reviewer "Research editor"

Run validation and retrospective report:

    python -m unittest discover -s intel/tests -v
    python -m intel.validate
    python -m intel.calibration

`intel/quality/forecast_calibration.json` counts registered, unresolved,
overdue, and binary editorially resolved forecasts. A Brier mean is shown
ONLY after at least five binary outcomes are adjudicated. Even a Brier mean
after five is sample-bound and not evidence of superiority to a baseline.
VOID outcomes are shown separately, never counted as correct.

Both new permanent editorial stores begin EMPTY. Historical observations
must not be backdated as forecasts and probabilities must never be chosen
after observing the outcome. Researchers may add genuine forecasts only
after independently reviewing the original evidence and freezing an
unambiguous testable proposition. The weekly audit surfaces overdue work
but is not proof an independent evidence review happened.


### CI immutability and retroactive-registration defense

Running the editorial CLI alone is not sufficient: a raw JSON edit could
otherwise change a previous predicted probability or rewrite a past review.

`python -m intel.guard_forecasts` now runs in source-collection CI and the
weekly audit, comparing the new commit with the first parent using Git
history. It rejects any deletion or modification to previously published
forecast or resolution records. Newly inserted forecasts must have an
honest registration timestamp no more than 48 hours before the commit and
no more than two hours in the future. Github Actions checkout fetches at
least two commits for this review. Existing records are treated as
immutable after publication.

This guards against ordinary accidental hindsight edits; it does NOT
prove original evidence was genuinely reviewed and is not a substitute
for human/Agent source verification. Editorial errors in a registered
forecast must be disclosed in a separate addendum or declared VOID with
an explicit reason, rather than silently changing the frozen original.
