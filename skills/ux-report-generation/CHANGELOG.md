# Changelog

All notable changes to the `ux-report-generation` skill are documented here.

---

## [1.4.0] — 2026-05-05

### Added

- **Section 2 — Scope & Assumptions** (new required section between Cover and Executive Summary). Placeholders: `[SCOPE_TEXT]`, `[ASSUMPTIONS_TEXT]`.
- **Section 9 — Confidence & Gaps** (new required section after Methodology). Placeholders: `[CONFIDENCE_LEVEL]`, `[CONFIDENCE_NARRATIVE]`, `[GAPS_TEXT]`.
- `docs/skill-customization-guide.md` — guidance for consuming skills on adapting the Findings section, scorecard mapping, Page column usage, and new section placement rules.
- `ai-ux-audit` added to the Folder and Naming Convention table in `SKILL.md`.
- `.skip-link` CSS component — keyboard-accessible skip-to-content link rendered at the top of every report.
- `@media (prefers-reduced-motion: reduce)` guard on `.jira-action-bar` transition and `.jira-config-toggle .arrow` transition (WCAG 2.1 §2.3.3).
- `tests/functional/test_multipage_audit.yaml` — validates Page column in multi-page audit reports.

### Changed

- **Heading hierarchy corrected** in `report-shell.html`:
  - `<div class="section-title">` → `<h2 class="section-title">` (all 5 section headings)
  - Category header `<h2>` → `<h3>`
  - Finding title `<h3>` → `<h4>`
  - Executive summary `<h2>Overview</h2>` → `<h3>`
  - Methodology cards `<h4>` → `<h5>`
- **Risk Banner** changed from `<div class="risk-banner">` to `<aside class="risk-banner" aria-label="Overall risk level">`. Internal `<h3>` replaced with `<p class="risk-title">`.
- **ARIA landmarks** added: `<main id="main-content">` wraps the report container; cover carries `role="banner"`; `<a href="#main-content" class="skip-link">` prepended to `<body>`.
- **`scripts/generate-pdf.mjs`**: Chrome executable path is now auto-detected across macOS, Linux (`/usr/bin/google-chrome`, chromium, snap), and Windows (`Program Files`). Falls back to Playwright's bundled Chromium when no local installation is found. Removes the macOS-only hardcoded path.
- **CSS selectors** updated to match new heading hierarchy: `.executive-summary h3`, `.category-header h3`, `.risk-banner .text .risk-title`, `.methodology-card h5`.
- Section numbering in `report-shell.html` comments updated (①–⑨).
- Section count in `report-contract.md` updated from 7 to 9 required sections.
- Version bumped to `1.4.0` in `SKILL.md`.

---

## [1.3.0] — Previous

Initial stable release. Established: 7-section contract, Density CSS token system, Playwright PDF export, Jira integration panel (styles + action bar), and 4 functional test cases.
