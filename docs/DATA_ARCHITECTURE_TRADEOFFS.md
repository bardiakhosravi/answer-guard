# Data Architecture Tradeoffs: Ingest vs. Federate

**Status:** Draft — decision pending
**Date:** 2026-04-22
**Related:** [PRD.md](./PRD.md), [ARCHITECTURE.md](./ARCHITECTURE.md)

Decision memo on whether AnswerGuard should copy the customer's Q&A corpus into its own database or read it directly from the customer's existing database via a field-mapping configuration.

---

## 1. Reframe the question

The naive framing — **"do we ingest data or connect directly?"** — is a false dichotomy.

AnswerGuard **always needs its own database**, regardless of where the Q&A corpus lives. We generate data that does not exist anywhere in the customer's system:

- **Annotations** — span offsets, issue types, severities, preferred rewrites, linked-feedback history
- **Guidelines** — rules, priorities, status, lifecycle, conflicts
- **Enforcement logs** — draft, final, latency, guidelines fired, confidence scores
- **Runtime Q&A** — responses flowing through the SDK/API in production (not in the customer's historical DB)

So the real architectural question is:

> **Where does the Q&A corpus itself live?** Inside our DB (copied), in the customer's DB (federated), or split across both (hybrid)?

And a secondary question that is usually invisible in the naive framing:

> **How do runtime responses (from the SDK) and historical responses (from the source DB) stay coherent?** If they live in different stores, we have a split-corpus problem worse than either pure option.

---

## 2. The three real options

### Option A — Copy (current PRD design)

- Source connector reads customer's Q&A into AnswerGuard's DB on bootstrap and delta sync.
- Runtime SDK writes also land in AnswerGuard's DB.
- Annotations, guidelines, logs reference AnswerGuard-local Q&A rows.
- Customer DB is **read-only, once**, for bootstrap; AnswerGuard is otherwise independent.

### Option B — Federate (read-through)

- Customer maps their schema: *"question is column X in table Y, answer is column Z in table W, joined by conversation_id."*
- AnswerGuard reads the corpus live from the customer's DB on every query.
- AnswerGuard's DB holds only annotations, guidelines, and enforcement logs.
- Annotations store `source_ref` pointers back to the customer's primary keys.
- Runtime SDK responses must still land somewhere — either pushed back into the customer's DB (requires write access + schema ownership) or into AnswerGuard's DB (creates split corpus).

### Option C — Hybrid (federate + local cache)

- Federate for freshness, materialize into AnswerGuard's DB for search/indexing.
- Customer DB is source of truth for historical; cache is invalidated on a sync cadence.
- Runtime SDK responses land in AnswerGuard's DB and optionally push to customer DB.

---

## 3. Tradeoff matrix

Scored for a v1 deployment where the customer has 100K–10M Q&A pairs, Postgres/MySQL/Mongo, and wants a PM-usable review UI plus runtime enforcement.

| Dimension | A — Copy | B — Federate | C — Hybrid |
|---|---|---|---|
| **Schema variance handling** | Canonicalize once at write | Canonicalize on every read — translation layer grows with each new customer | Same as A for the cached part |
| **Indexing control** (FTS, vector, partial indexes) | Full control | None — must ask customer's ops | Full control over cache |
| **Query performance** | Predictable | Depends on customer DB tuning, load, network | Predictable on cache, degrades on cache miss |
| **Read load on customer's production DB** | Zero after bootstrap | Linear with PM and enforcement traffic | Low, but nonzero on sync |
| **Data freshness** | Delta sync cadence (minutes–hours) | Real-time | Depends on cache TTL |
| **Ingestion adapters to build** | 1 per source type (Postgres, MySQL, Mongo, BigQuery, …) | 1 per source type | 1 per source type + cache invalidation logic |
| **Annotation FK integrity** | Stable — annotation points to AnswerGuard-local PK | Fragile — if customer deletes/renames a row, annotation dangles | Stable on cache, fragile on source-only records |
| **Runtime-vs-historical corpus coherence** | Single store, trivially coherent | Split corpus unless we push back to customer DB | Single store (cache + runtime both in AnswerGuard DB) |
| **Procurement narrative** ("you're copying our data") | Negative — but mitigated by self-hosted deployment | Positive | Neutral — requires explanation |
| **Data residency / PII** | Customer's own infra (self-hosted), so identical to B in practice | Customer's own infra | Customer's own infra |
| **Storage cost** | Duplicate corpus storage | No duplication | Partial duplication |
| **Failure coupling to customer DB** | Decoupled after bootstrap | Tightly coupled — our uptime ≤ their DB uptime | Partially coupled |
| **Future features enabled** | Vector search, embeddings, analytics, synthesis, export | Most blocked without replicating to our store anyway | Most enabled |
| **v1 engineering effort** | Lower — one code path, known schema | Higher — per-backend query builder, schema-mapping UI, runtime push-back | Highest — both paths plus invalidation |
| **Debuggability** | Local, reproducible | Requires customer DB access to reproduce | Mixed |
| **Schema evolution velocity** | Independent of customer | Blocked on customer changes | Independent for cache |

---

## 4. Where each option breaks down

### Option A — Copy

Where it hurts:
- **Bootstrap pain for large corpora.** 10M+ Q&A records = hours of copy time and non-trivial storage. Needs delta sync and idempotent ingestion.
- **Customer objection.** "Why are you copying our data?" is a procurement conversation. Self-hosted deployment mitigates this — the copy lives in the customer's own infra, not ours — but we have to tell that story clearly.
- **Staleness.** If the customer updates an answer in their CRM and the PM reviews a stale version in AnswerGuard, trust erodes.

These are solvable with standard ETL hygiene. None are architecturally fatal.

### Option B — Federate

Where it breaks:

1. **"Just pick two columns" is a lie.** Real customer schemas look like:
   - Q&A in separate tables joined by `conversation_id`.
   - Multi-turn conversations where the "question" is a thread of messages.
   - Tool calls, reasoning steps, and final answer stored separately.
   - Drafts, revisions, user edits.
   - Metadata (user ID, topic, timestamps) spread across three joins.

   A two-field mapping UI does not handle this. You will end up building a mapping DSL — which is more complex than ingesting.

2. **Runtime splits the corpus.** SDK-generated responses must land somewhere. Writing them back into the customer's schema requires write access, schema ownership, and a migration path for their tables — a non-starter. Landing them in AnswerGuard's DB instead means historical and runtime responses live in different stores with different schemas. Every query against "all responses" now has to federate **across two backends**. Every annotation UI has to handle two ID spaces. This is the worst of both worlds.

3. **You can't add the indexes you need.** pgvector, GIN full-text, partial indexes for filtering by topic/severity, materialized aggregates for reporting — none of these can be added to a customer's production DB without becoming a stakeholder in their DB lifecycle. That's the wrong boundary.

4. **Annotation integrity is at the customer's mercy.** If they delete or re-key a row, your annotations dangle. You have no ability to enforce referential integrity across DBs.

5. **Read load on production.** Every time a PM browses the review UI, you're hitting the customer's operational database. Enforcement analytics queries hit it harder. You become an uptime stakeholder for a system you don't own.

6. **Per-backend engineering tax.** You still need an adapter per source (Postgres, MySQL, Mongo, BigQuery, Snowflake, S3). The adapter is harder in the federate model because it must support arbitrary query shapes, not just bulk extract.

### Option C — Hybrid

Where it breaks:
- Requires all the ingestion work of A plus cache-invalidation logic.
- Only justified when a specific customer rejects Option A outright and a specific use case demands real-time source freshness.
- Do not build this for v1 — it's a v2 deployment mode for a specific customer need that may never materialize.

---

## 5. Future-lookahead — what each option enables or blocks

| Future feature | A — Copy | B — Federate |
|---|---|---|
| **Automated guideline synthesis from feedback** (the v1-critical feature per competitive analysis) | Requires embeddings + clustering over the corpus — straightforward | Requires replicating to our store anyway → effectively Option A |
| **"Top failure modes" PM reporting** | Standard aggregation on our DB | Aggregation across federated backends; slow and brittle |
| **Vector / semantic search over historical responses** | pgvector on our DB | Blocked without replication |
| **Training data export** (for customer's own fine-tuning) | Single canonical schema, clean export | Must materialize first |
| **Cross-customer benchmarks** (if we ever go multi-tenant SaaS) | Possible with consent | Blocked |
| **Guideline-preview against historical** | Fast — runs entirely in our DB | Requires federated scan per preview |
| **Rewrite fidelity checks** (fact-preservation diffing) | Trivial lookup | Requires live federated read |
| **Runtime enforcement logs as a reviewable corpus** | Same store as historical — unified review | Split corpus unless we push back |
| **Quality regression detection** over time | Windowed aggregation on our DB | Requires federated time-series queries |

Every future feature that is interesting **requires the corpus to live in our DB eventually**. Federate buys a shorter time-to-first-demo and a nicer procurement pitch; it pays for both by blocking the features that make the product competitive.

---

## 6. Ruthless challenges to the "just connect" framing

Since this is the side you're leaning toward for elegance:

**a) "We just visualize and capture feedback in v1" is a v1 scope argument, not an architecture argument.** v1 scope changes. Architecture is harder to change. Optimizing architecture for v1 scope is how products ship with data layers that have to be rewritten by v3.

**b) "Customers prefer we don't copy their data" is often asserted, rarely validated.** The actual customer objection is usually "don't exfiltrate our data to your cloud." Self-hosted deployment answers that completely. The copy lives in their VPC, on their Postgres, under their backup policy. If you pitch it as "we stand up a read-model in your infra," the objection usually disappears.

**c) "Federation is more elegant" is aesthetic, not economic.** The economics favor copy for every feature beyond pure visualization. The elegance has a price you'll feel on feature #4.

**d) "Schema mapping UI" is a product you're quietly signing up to build.** It will have ongoing maintenance cost, customer support cost ("my mapping broke when we migrated to a new schema"), and an error-mode surface area larger than the ingestion connector it replaces.

**e) Hexagonal architecture is on your side only if you use it right.** The source Q&A is a **secondary outbound port** (`QAResponseSourcePort` or similar). The adapter behind it can be `CopyingSourceAdapter` in v1 and `FederatedSourceAdapter` in v2 for a specific customer. Choose the simpler adapter first; keep the port stable. You don't need to commit to federate in v1 to keep federate as a deployment option.

**f) "Runtime SDK data has to land somewhere" is the argument that usually kills federate in practice.** Teams propose federate when they're thinking about the historical review UI, forget about the runtime enforcement path, and discover mid-build that they've committed to a split corpus.

---

## 7. Recommendation

**Ship v1 with Option A (Copy) behind a clean port.**

Concretely:

1. **Define `QAResponseSourcePort`** in the domain layer. Operations: bulk extract, delta extract by watermark, single record lookup by source ref.
2. **V1 adapter: `PostgresCopyingSourceAdapter`.** Reads customer's Postgres, canonicalizes into AnswerGuard's `qa_response` table. Preserves `source_system`, `source_ref`, `raw_payload` (jsonb) for forensics.
3. **Canonical schema in AnswerGuard's DB:**
   - `qa_response` — canonical question, answer, timestamps, metadata jsonb
   - `qa_response_source_link` — source_system, source_ref, last_synced_at, content_hash
   - `annotation` — FK to `qa_response.id` (local PK, never to source ref)
   - `guideline`, `enforcement_log` — as specified in PRD
4. **Delta sync on a configurable cadence** using an updated-at watermark. Recompute `content_hash` to detect in-place edits.
5. **Runtime SDK writes land in the same `qa_response` table** with `source_system = 'answerguard_runtime'`. Unified corpus, no split.
6. **Keep Option B (Federate) as an explicit v2 deployment mode**, triggered only if a specific customer's data-sensitivity posture makes Option A a dealbreaker that self-hosted deployment does not resolve. At that point, implement `FederatedSourceAdapter` behind the same port; AnswerGuard's own DB still holds annotations/guidelines/logs.

### Reframe the customer conversation

Do not sell Option A as "we copy your data." Sell it as:

> *"AnswerGuard runs entirely in your infrastructure. We stand up a read-model of your Q&A corpus in your own Postgres database — the one you provision and back up — so that the review UI and enforcement engine can run without putting read load on your production CRM/support DB. Your data never leaves your VPC."*

This is true, architecturally clean, and removes the "are you copying our data?" objection.

### What to build in v1 to keep Option B viable later

- Source port is abstract, not Postgres-shaped.
- Annotations reference AnswerGuard-local Q&A PKs, with `source_ref` preserved on the Q&A record for traceability — never on the annotation directly.
- Ingestion is a discrete, swappable component in the DI container.
- Canonicalization logic (customer schema → canonical Q&A) lives in the adapter, not in domain or use cases.

These choices cost nothing in v1 and keep federate open as a future deployment mode without committing to it.

---

## 8. What would change this recommendation

I'd revisit if any of these are true:

- **A real customer** (not a hypothetical) explicitly says copy-to-their-own-Postgres is a dealbreaker after seeing the self-hosted pitch.
- **Corpus size > 100M records** where delta sync operational cost dominates development velocity.
- **v1 scope shrinks to pure visualization** with no runtime enforcement, no analytics, no synthesis — in which case federate is defensible because future features don't exist to block. But that's not your v1.
- **Regulatory constraint** (e.g., HIPAA with specific replication restrictions) that makes even an in-VPC read-model non-compliant. Rare; would require legal review.

Absent those, Option A is the decision.

---

## 9. Next step

If this analysis lands, convert the decision into an ADR: `docs/ADR/0001-copy-source-qa-into-answerguard-db.md`. Per the project's tenets rules, database/architecture decisions of this scope warrant one.
