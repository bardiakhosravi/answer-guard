# Implementation Plan: Developer Documentation

**Branch**: `002-developer-docs` | **Date**: 2026-04-22 | **Spec**: [spec.md](./spec.md)

---

## Summary

Build and publish the AnswerGuard developer documentation site using **Docusaurus v3** (classic preset, TypeScript), hosted on **GitHub Pages**. The site covers: overview, SQLite-only quickstart, full integration guide (BigQuery + Python SDK + TypeScript SDK), REST API reference, configuration reference, and troubleshooting. A GitHub Actions workflow publishes automatically on every push to `main`.

**Published URL**: `https://bardiakhosravi.github.io/answer-guard/`

---

## Technical Context

**Framework**: Docusaurus v3, classic preset, TypeScript
**Hosting**: GitHub Pages (`gh-pages` branch, auto-deployed via GitHub Actions)
**Content format**: Markdown / MDX in `website/docs/`
**Search**: `@docusaurus/plugin-search-local` (offline, no API key)
**Local preview**: `npm run start` in `website/` (live-reload)
**Node.js version**: 20 LTS
**Deployment action**: `peaceiris/actions-gh-pages`
**PR enforcement**: `.github/pull_request_template.md` with doc update checkbox (FR-011)
**Quickstart database**: SQLite only (no Docker)

---

## Constitution Check

Documentation + CI/CD feature — Hexagonal Architecture rules do not apply.

| Principle | Status | Notes |
|-----------|--------|-------|
| Documentation co-located with source | PASS | `website/` lives in the same repo alongside `src/` |
| Documentation updates required with code changes | PASS | PR template enforces this on every PR |
| No implementation details in spec | PASS | Docusaurus/GitHub Pages chosen post-spec in planning phase |

---

## Project Structure

```
website/                              # Docusaurus project root
├── docs/
│   ├── intro.md                      # Overview + value proposition
│   ├── quickstart.md                 # SQLite-only quickstart (≤30 min)
│   ├── integration/
│   │   ├── index.md                  # Integration overview
│   │   ├── bigquery.md               # BigQuery source configuration
│   │   ├── historical-import.md      # Running the bulk import
│   │   ├── python-sdk.md             # Python SDK runtime capture
│   │   ├── typescript-sdk.md         # TypeScript SDK runtime capture
│   │   └── verification.md           # Verifying the integration
│   ├── reference/
│   │   ├── api.md                    # REST API reference (all endpoints)
│   │   └── configuration.md          # All config options + env vars
│   └── troubleshooting.md            # Common errors + resolutions
├── src/
│   └── pages/
│       └── index.tsx                 # Custom landing page (hero + CTA)
├── static/
│   └── img/
│       └── answerguard-flow.png      # Data flow diagram
├── docusaurus.config.ts              # Site config
├── sidebars.ts                       # Sidebar nav definition
└── package.json

.github/
├── workflows/
│   └── docs.yml                      # Build + deploy to GitHub Pages on push to main
└── pull_request_template.md          # PR checklist with doc update requirement
```

---

## Key Implementation Notes

### Docusaurus initialisation
Run `npx create-docusaurus@latest website classic --typescript` to scaffold the project, then replace the generated content with AnswerGuard documentation. Delete the generated blog and example pages — AnswerGuard does not need a blog for v1.

### `docusaurus.config.ts` key settings
```typescript
{
  title: 'AnswerGuard',
  tagline: 'Response quality enforcement for AI agent products',
  url: 'https://bardiakhosravi.github.io',
  baseUrl: '/answer-guard/',
  organizationName: 'bardiakhosravi',
  projectName: 'answer-guard',
  trailingSlash: false,
  themeConfig: {
    navbar: { /* Overview, Quickstart, Integration, Reference, GitHub */ },
    prism: { theme: lightCodeTheme, darkTheme: darkCodeTheme },
  },
}
```

### GitHub Actions deployment
`.github/workflows/docs.yml`:
- Trigger: `push` to `main` (path filter: `website/**` or `docs/**`)
- Steps: checkout → Node.js 20 → `npm ci` (in `website/`) → `npm run build` → `peaceiris/actions-gh-pages` deploying `website/build/` to `gh-pages` branch
- First deploy: manually enable GitHub Pages in repo Settings → Pages → Source: `gh-pages` branch

### PR template
`.github/pull_request_template.md` includes:
```
- [ ] If this PR changes any documented behaviour (API fields, config options,
      SDK methods, error messages), the relevant page in `website/docs/` has been updated.
```

### Content accuracy
All API field names, types, defaults, and endpoint paths in `website/docs/reference/api.md` must match `specs/001-qa-response-ingestion/contracts/api.md` exactly. Reference the contracts file as the authoritative source when writing the reference page.

### Quickstart test capture
The quickstart uses `curl` or `httpie` to send a test `POST /v1/capture` request immediately after starting the server — no BigQuery credentials needed. This gives the developer visible data in storage within the quickstart flow itself.

### Custom landing page
`src/pages/index.tsx` is a React component that renders a hero section with: title, tagline, "Get Started" CTA button (links to quickstart), and "View on GitHub" button. Docusaurus provides the `useDocusaurusContext` hook and standard layout components for this.

---

## Verification

1. **Local preview**: `cd website && npm run start` — no errors; all sidebar links resolve; code blocks have copy buttons; search returns results.
2. **Production build**: `npm run build` completes with zero broken links (`--no-trailing-slash` mode).
3. **GitHub Pages deploy**: Push to `main` triggers `docs.yml`; site is live at `https://bardiakhosravi.github.io/answer-guard/` within 3 minutes.
4. **Quickstart validation**: Follow the quickstart from a clean Python 3.11 environment; verify a running instance and a captured Q&A pair appearing in the status endpoint within 30 minutes.
5. **Navigation contract**: Every page in `specs/002-developer-docs/contracts/navigation.md` exists and appears in the sidebar.
6. **Reference accuracy**: Every field in `website/docs/reference/api.md` matches `specs/001-qa-response-ingestion/contracts/api.md`.
7. **PR template**: Open a test PR; confirm the documentation checklist item is visible.

---

## Complexity Tracking

*No architecture violations. Docusaurus is entirely in `website/` — no coupling to the Python backend.*
