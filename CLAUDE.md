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

## Active Technologies
- Python 3.11+ (backend API + BigQuery connector), TypeScript 5.x (SDK) + FastAPI, SQLAlchemy 2.0 (sync), Alembic, `google-cloud-bigquery`, `pydantic` (001-qa-response-ingestion)
- PostgreSQL (production), SQLite (local dev) — same schema via SQLAlchemy dialects (001-qa-response-ingestion)
- Docusaurus v3 (TypeScript, classic preset), GitHub Pages, GitHub Actions (002-developer-docs)

## Recent Changes
- 001-qa-response-ingestion: Added Python 3.11+ (backend API + BigQuery connector), TypeScript 5.x (SDK) + FastAPI, SQLAlchemy 2.0 (sync), Alembic, `google-cloud-bigquery`, `pydantic`
- 002-developer-docs: Added Docusaurus v3 (TypeScript) + GitHub Pages deployment via GitHub Actions
