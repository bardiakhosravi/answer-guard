# Data Architecture — Ingest vs. Direct-Connect Tradeoff Analysis

**Status:** Draft
**Author:** Principal PM review
**Related:** [PRD.md](./PRD.md), [ARCHITECTURE.md](./ARCHITECTURE.md), [COMPETITIVE_ANALYSIS.md](./COMPETITIVE_ANALYSIS.md)

---

## 1. Framing the decision cleanly (it's not actually binary)

Before the tradeoff, reframe: there are **three options**, not two. The PRD implies a binary, and that's the first mistake.

| Option | Historical Q&A | New Q&A (via SDK) | Annotations / Guidelines / Logs |
|---|---|---|---|
| **A. Full ingest** (current PRD) | Pulled into AG DB | Written to AG DB | AG DB |
| **B. Direct connect** | Queried live from customer DB | Written to AG DB | AG DB |
| **C. Hybrid (federated)** | Indexed in AG DB, source-of-truth in customer DB, on-demand hydration | Written to AG DB | AG DB |

Crucial point: **annotations, guidelines, and enforcement logs are always ours** regardless of option. The debate is *only* about the historical Q&A corpus. New runtime data already flows into AG's DB through the SDK per §5 of the PRD, so the ingest pipeline exists either way — direct-connect doesn't eliminate it, it only shrinks what flows through it.

---

## 2. Tradeoff matrix

Rating: ✅ advantage · ⚠️ tolerable · ❌ problematic

| Dimension | A. Ingest | B. Direct connect | C. Hybrid |
|---|---|---|---|
| Data freshness | ⚠️ stale between syncs | ✅ always fresh | ✅ fresh on hydration |
| Query performance (PM browsing, search, faceting) | ✅ we own indexes | ❌ at mercy of their schema | ✅ indexed in AG |
| Schema coupling to customer | ✅ decoupled | ❌ breaks on their rename/restructure | ⚠️ soft coupling via key |
| Derived data (embeddings, topics, scrubbed PII, quality scores) | ✅ first-class | ❌ requires sidecar tables anyway | ✅ first-class |
| Full-text / semantic search | ✅ trivial with pg_trgm/pgvector | ❌ depends on their engine (MySQL 5.7? Dynamo?) | ✅ |
| Load on customer production DB | ✅ one-time pull | ❌ every PM browse/filter hits prod | ⚠️ hydration only |
| Credential & network surface | ✅ pull once, done | ❌ persistent read creds, VPC, rotation | ⚠️ persistent but low-volume |
| Compliance / data custody | ❌ we custody their data (GDPR surface) | ✅ we don't | ⚠️ we custody less |
| Right-to-erasure | ❌ two delete targets | ✅ delete in their DB = gone | ⚠️ delete propagation required |
| Data drift (they edit a record) | ❌ our copy goes stale; annotations misalign | ✅ always reflects latest | ⚠️ detectable via hash |
| Onboarding time-to-first-value | ⚠️ need connector pipeline | ✅ field mapping form | ⚠️ field mapping + hydration |
| Multi-source reality (agents don't have one Q&A table) | ✅ we normalize | ❌ falls apart fast | ✅ we normalize |
| Feature velocity (next 18 months) | ✅ we own the substrate | ❌ every feature = sidecar | ✅ we own the substrate |
| Future SaaS offering (answerguard.cloud) | ✅ works | ❌ can't reach into their prod from SaaS | ⚠️ works if they expose a read endpoint |
| Annotation durability when source row deleted/mutated | ✅ snapshot in AG | ❌ orphaned annotations | ⚠️ snapshot via hydration |

Scoreboard: Ingest wins on 10, Direct wins on 4, Hybrid wins or ties on most of both sides.

---

## 3. The five questions that actually decide this

A matrix is useless without weighting. These questions determine which column matters:

1. **Is the PM going to search/filter/sort over the historical corpus, or just open specific responses they already know about?**
   - If search → Ingest or Hybrid wins by a mile. Direct-connect is a disaster at 100K+ rows without indexes we don't control.
   - If opening-by-ID only → Direct-connect is viable.

2. **Do agent systems in the target market actually have a single, well-structured Q&A table?**
   - Reality check: most don't. Questions come from Zendesk/Intercom, responses from a vector store trace, context from a product DB, feedback from a human handoff system. Direct-connect assumes a fiction that rarely exists.
   - If customers mostly log to one nice table → Direct-connect viable. If they have a trace stack → Ingest only.

3. **Is derived data (embeddings, topic clusters, PII scrubs, span-level labels) needed in v2?**
   - If yes (and it is — §4 of PRD implies it, automated guideline synthesis requires it) → Ingest. Derived data on top of direct-connect is a sidecar table pretending to be a database.

4. **What's the compliance posture of the target enterprise?**
   - If they're a bank/health/EU-regulated → "we don't store your data" is a real selling point. Direct-connect can win enterprise deals Ingest will lose.
   - If they're a mid-market SaaS → they don't care. Ingest is fine.

5. **Is answerguard.cloud on the 18-month roadmap?**
   - If yes → Ingest, hard. SaaS can't reach into customer prod DBs without a reverse tunnel or a data plane agent, which is huge complexity. If a cloud offering is the real business model, direct-connect is a dead end.
   - If self-hosted forever → Direct-connect stays viable.

---

## 4. Failure modes

The "I wish I'd known" items.

### Direct-connect failure modes

- **Schema drift.** Customer renames `response_text` → `final_answer` in a Friday deploy. UI is broken Monday. Support tickets for a thing we didn't change.
- **Missing indexes.** A PM filter on `topic LIKE 'billing%' ORDER BY created_at DESC` triggers a full table scan against their prod DB. Their DBA calls. Tool gets disabled.
- **PII we can't remove.** Customer asks "can you mask SSNs in the review UI?" We can't — we don't control the data. We rebuild in a sidecar → we're now partially ingesting anyway.
- **Annotation orphaning.** They TTL-delete rows after 90 days. PM's carefully-crafted annotations from 6 months ago point at ghosts. If we snapshot on annotation → we're ingesting selectively → we invented Hybrid.
- **No single Q&A table.** "The question is in `conversations.messages[0].content` where `role='user'`, the answer is… it depends on which agent handled it…" The field-mapping form becomes a query builder.
- **Multi-tenant customer DBs.** Their Q&A table has a `tenant_id` column. Mapping config is per-tenant. Rapidly a mess.

### Ingest failure modes

- **Sync lag.** PM annotates a response that's been edited in production. Their feedback applies to text that no longer exists. Mitigation: store a content hash and flag "source has changed since you annotated this."
- **Storage cost.** At 10M historical Q&A pairs × ~2KB each = ~20GB. Manageable. At 1B, less so. Handle with archival tiering.
- **Data custody = compliance surface.** Need DPA, SOC 2, possibly EU residency. Direct-connect skips all of that. Real cost, real sales friction for certain buyers.

---

## 5. The Hybrid (option C) — what it actually looks like

This is the option the PRD should probably land on.

- **On ingestion**: pull `(source_row_id, content_hash, question, answer, core metadata)` into AG's `qa_pairs` table. Store source content. Index for search, filtering, embeddings.
- **On display**: show AG's cached version. Overlay a "verify against source" link that does a live read against the customer DB to detect drift (via content hash).
- **On annotation**: snapshot the exact text that was annotated into the annotation row — so annotations survive source mutation/deletion.
- **On derived features** (embeddings, topics, PII scrubs, quality scores): write to AG. First-class.
- **On deletion**: a delete-propagation webhook or scheduled reconciliation job. Customer deletes row → we soft-delete in AG within 24h. GDPR-friendly enough for most, defensible in a DPA.
- **On customer DB access**: read-only, low-volume, only on demand ("verify source") or scheduled reconciliation. Not on every PM click.

The operational model: **AG's DB is the serving layer and the feature substrate. The customer DB is the source of truth that AG periodically reconciles against.**

This is the same pattern Segment, Fivetran, Hightouch, Airbyte, and every CDP/ETL tool converged on — because the alternative (direct query against source of truth) doesn't survive contact with real customer data.

---

## 6. Future-facing considerations that change the math

Things v1 doesn't force but v2/v3 will need. These all push toward ingest/hybrid.

1. **Automated guideline synthesis** (explicitly deferred in PRD but the real product). Needs embeddings of all responses, clustering of failure modes, batch LLM analysis over the corpus. None of this is possible on direct-connect without a shadow copy.
2. **Regression preview** ("what would activating this guideline have changed across the last 10K responses?"). Needs batch processing over historical data. Needs to be fast. Direct-connect = their prod DB is our batch engine, which it isn't.
3. **Topic auto-classification for guideline scoping** (Open Question #2 in PRD). Needs embeddings + classification pipeline. Sidecar territory.
4. **Quality metrics over time** ("tone compliance trend by category over 90 days"). Aggregation over large corpus. Direct-connect chokes.
5. **Span-level index.** The PRD's core UX is highlighting a sentence. We'll want tokenized, positioned, searchable spans. No customer DB will give us that. We're building it in AG regardless.
6. **Cross-tenant benchmarking (SaaS future).** Comparing one customer's failure patterns to anonymized aggregate. Impossible without ingest.
7. **Training data for the rewrite model itself.** If Tier 3 rewrite fidelity becomes a real problem, we'll want to fine-tune on (draft, guideline, accepted_rewrite) triples. We need that data, structured, in our control.

---

## 7. Recommendation

**Go Hybrid (option C), but *market* the ingest-minimization story.**

Concretely:

- **Architecture decision**: AG's Postgres is the serving and feature substrate. Historical ingest is real and required. Don't apologize for it.
- **Mitigate the "we store your data" objection** by making the minimum-necessary-data posture explicit in the product: configurable column allow-list, optional PII scrubbing at ingest, short retention defaults, delete-propagation webhook, content hashing for drift detection.
- **Keep the direct-connect connector as a narrow feature**, not the architecture: "verify against source" for a single record, scheduled reconciliation, delete propagation. Not the primary data path.
- **Kill the "field mapping form as onboarding" idea.** Real customers don't have one Q&A table. Build ingestion adapters per-source-type (OpenAI trace, Langfuse trace, generic webhook, CSV batch, SQL query template) rather than a generic field-mapper. The SDK is already the preferred path; make the historical connectors match.
- **Revisit this decision if** initial design partners are all regulated enterprises (banks, health, EU pharma) who contractually cannot let us custody data. In that world, direct-connect might need to be a supported deployment mode — but it will be a worse product and should be priced as such.

### One-sentence summary

Direct-connect sounds elegant and sells a compliance story, but it collapses the moment we need search, derived data, historical preview, or automated guideline synthesis — all of which are on our roadmap — so ingest (with hybrid reconciliation on top) is the load-bearing choice, and the compliance concerns are better solved with data-minimization controls than with architectural asceticism.

---

## 8. Open questions to resolve with design partner(s)

1. What's the actual shape of their agent trace? One table, or a stack?
2. Their approximate corpus size today and in 12 months (rows and bytes)?
3. Contractual constraints on data custody? DPA required? Region lock?
4. Retention policy on their side (do they TTL-delete)?
5. Who owns the customer DB — engineering, data platform, a vendor? This determines whether we get the read creds at all.
6. Is a read replica available, or only prod?
7. SaaS appetite: would they use answerguard.cloud if it existed in 12 months, or is self-hosted non-negotiable?
