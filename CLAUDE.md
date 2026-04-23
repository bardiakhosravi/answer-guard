# CLAUDE.md

<!-- tenets:start -->
## Architecture: Hexagonal + DDD (via tenets)

This project follows **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design**.
Rules are installed by `tenets`. Run `npx tenets update` to update.

### Non-negotiable rules
- **Dependency direction is inward**: adapters -> application -> domain. NEVER domain -> infrastructure.
- **Domain layer has ZERO external dependencies** — no frameworks, no ORMs, no HTTP libraries.
- **All infrastructure access goes through ports** (abstract interfaces).
- **Aggregates are the only entry point** for state mutations within their boundary.
- **Use cases orchestrate domain logic** — they contain NO business rules themselves.
- **Primary adapters translate** external requests to domain commands; they contain NO business logic.
- **Secondary adapters implement ports** — they handle all external system complexity.
- **Domain events use ubiquitous language only** — no vendor or technology names.

### Context-aware rules
Rules auto-load based on what you're editing:
- Editing `domain/` files -> domain rules load automatically
- Editing `adapters/` or `infrastructure/` files -> port & adapter rules load
- Editing `application/` files -> use case & orchestration rules load

### Automatic architecture review
After completing any feature implementation, bug fix, or refactoring that touches domain, application, or infrastructure code, you MUST run `/tenets-review-architecture` to verify compliance before presenting the work as done. Do not skip this step.

### On-demand review
You or the user can also run `/tenets-review-architecture` at any time for a full compliance audit.

Detailed rules: `.claude/rules/tenets-*.md`
<!-- tenets:end -->

## Active Bounded Context — Agent Governance

AnswerGuard has **one** bounded context: **Agent Governance**. Its purpose is to guard against bad agent responses reaching users — capturing them, collecting PM feedback on them, and (forthcoming) using that feedback to improve future responses.

Aggregates within Governance:

| Aggregate | Role |
|---|---|
| `QAPair` | An observed agent↔user exchange being governed |
| `IngestionRun` | Bookkeeping of a historical-import operation — supporting entity |
| `SourceConnector`, `FieldMapping` | Value objects configuring external data sources |
| `ResponseFeedback` | PM-authored feedback about a specific agent answer — what's wrong and what the agent should do instead. Independent aggregate; references the source `QAPair` by ID as provenance, not ownership. What we do with this data (synthesize guidelines, run enforcement, etc.) is a future concern |

Do **not** treat "Ingestion" or "Review" or "Adherence" as separate bounded contexts. They are mechanisms within Governance, not spheres of language of their own. If you're writing a docstring that would say "in the ingestion context," say "in the Governance context."

## Active Technologies

- Python 3.11+, FastAPI, SQLAlchemy 2.0 (sync), Alembic, `google-cloud-bigquery`, `pydantic-settings`, `httpx`, `psycopg2-binary` (backend)
- PostgreSQL (production), SQLite (local dev) — same schema via SQLAlchemy dialects
- TypeScript 5.x, React 18, Tauri v2, React Router v6, React Query, React Hook Form, Tailwind CSS (desktop app)
- Docusaurus v3 (TypeScript, classic preset), GitHub Pages, GitHub Actions (developer docs)

## Recent Changes

- 004-response-improvement: `ResponseFeedback` aggregate added to the Governance context — PM captures feedback on agent answers via text selection in the desktop app; feedback references the source `QAPair` by ID (provenance only)
- 003-desktop-integration-setup: Tauri desktop app for source setup, import, and data view
- 002-developer-docs: Docusaurus developer docs site deployed to GitHub Pages
- 001-qa-response-ingestion: Ingestion aggregates (`QAPair`, `IngestionRun`) + BigQuery connector + SDKs
