# Research: Developer Documentation

**Feature**: 002-developer-docs
**Date**: 2026-04-22

---

## Decision 1: Static Site Generator — Docusaurus

**Decision**: Use Docusaurus (v3, classic preset, TypeScript).

**Rationale**:
- Industry standard for open source developer documentation — used by React, Jest, Babel, Vercel, Supabase, and hundreds of OSS projects
- TypeScript support out of the box (fits the existing TypeScript SDK in this repo)
- MDX support: embed React components in Markdown when richer content is needed
- Built-in versioned docs (important as AnswerGuard adds API versions)
- Built-in search (local search via `@docusaurus/plugin-search-local` for v1; Algolia DocSearch later)
- Excellent GitHub Pages deployment story via official `@docusaurus/plugin-pages` + `USE_SSH` flag
- `npm run start` gives a live-reloading local preview

**Alternatives considered**: MkDocs Material (Python, excellent for Python-only projects but adds a Node.js build step anyway for assets; weaker MDX story), plain GitHub Markdown (no search, no navigation, poor reading UX for multi-page docs).

---

## Decision 2: Project structure — `website/` subdirectory

**Decision**: The Docusaurus project lives in `website/` at the repo root. Documentation content lives in `website/docs/`.

**Rationale**: The repo already has a Python backend at the root and a `docs/` directory with internal project documents (PRD.md, ARCHITECTURE.md). Putting Docusaurus in `website/` keeps concerns cleanly separated and is the convention used by Meta's own open source projects (React, Relay, etc.).

```
website/
├── docs/                       # All developer documentation (Markdown / MDX)
│   ├── intro.md                # Overview + landing content
│   ├── quickstart.md
│   ├── integration/
│   │   ├── index.md
│   │   ├── bigquery.md
│   │   ├── historical-import.md
│   │   ├── python-sdk.md
│   │   ├── typescript-sdk.md
│   │   └── verification.md
│   ├── reference/
│   │   ├── api.md
│   │   └── configuration.md
│   └── troubleshooting.md
├── src/
│   └── pages/
│       └── index.tsx           # Custom landing page (optional for v1)
├── static/
│   └── img/                    # Diagrams, screenshots
├── docusaurus.config.ts        # Site config (title, nav, GitHub links)
├── sidebars.ts                 # Sidebar navigation definition
└── package.json
```

---

## Decision 3: Hosting — GitHub Pages via GitHub Actions

**Decision**: Deploy to GitHub Pages using the official Docusaurus GitHub Actions workflow. The `gh-pages` branch is managed automatically.

**Workflow**: `.github/workflows/docs.yml` — triggers on push to `main`. Steps: checkout → setup Node.js 20 → `npm ci` in `website/` → `npm run build` → deploy to `gh-pages` branch using `peaceiris/actions-gh-pages`.

**Published URL**: `https://bardiakhosravi.github.io/answer-guard/`

---

## Decision 4: Quickstart database path

**Decision**: SQLite only — no Docker required (confirmed by user in clarification session). PostgreSQL setup is covered separately in the integration guide.

---

## Decision 5: FR-011 enforcement — PR template

**Decision**: `.github/pull_request_template.md` with a mandatory documentation checklist item. Human-enforced, zero additional tooling for v1.

---

## Decision 6: Search

**Decision**: `@docusaurus/plugin-search-local` for v1 (offline, no API key required). Algolia DocSearch is a future upgrade when the site has meaningful traffic.
