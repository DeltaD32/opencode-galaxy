# Skill Customisation Guide

This document explains how each consuming skill should adapt the `report-shell.html` template. The contract (required sections, Density tokens, heading hierarchy) is fixed. The structure _inside_ the **Findings** section is the primary customisation point.

---

## Fixed Contract — Do Not Change

These elements must appear in every report exactly as specified in `report-contract.md` and `report-shell.html`:

- Section order (Cover → Scope & Assumptions → Executive Summary → Scorecard → Risk Banner → Findings → Priority Remediation Matrix → Methodology → Confidence & Gaps)
- All CSS custom properties (no hardcoded hex colours, spacing, or font sizes)
- Heading hierarchy (`h1` in cover → `h2` section headings → `h3` category → `h4` finding → `h5` methodology cards)
- Skip link, `<main id="main-content">`, `role="banner"` on cover

---

## Per-Skill Customisation Points

### 1. Findings Section — Category and Finding Cards

The category/finding card structure is the same across all skills, but the **content of badges and evidence** varies.

| Consuming Skill                                   | Category name maps to                                       | Finding title maps to         | Status badge maps to            |
| ------------------------------------------------- | ----------------------------------------------------------- | ----------------------------- | ------------------------------- |
| `nielsen-heuristics-ux-audit`                     | Nielsen heuristic (e.g. "H1 — Visibility of System Status") | Specific violation found      | Pass / Partial / Fail / Unknown |
| `ai-heuristics`                                   | AI heuristic group (e.g. "Transparency")                    | Individual AI principle check | Pass / Partial / Fail / Unknown |
| `ai-ux-audit`                                     | AI UX audit group (e.g. "Trust & Understanding")            | Individual audit criterion    | Pass / Partial / Fail / Unknown |
| `situational-awareness-design`                    | SA level (e.g. "Level 1 — Perception")                      | SA demon or design finding    | Pass / Partial / Fail / Unknown |
| `user-feedback-analysis`                          | Feedback theme (e.g. "Navigation Pain Points")              | Specific user complaint       | High / Medium / Low (frequency) |
| `ux-writing`                                      | Copy category (e.g. "Error Messages")                       | Specific copy issue           | Pass / Partial / Fail           |
| `hci-design-skills-for-genAI-chatbot-development` | HCI principle group                                         | Individual guideline check    | Pass / Partial / Fail / Unknown |

### 2. Scorecard — Count Labels

The four score boxes use **Pass / Partial / Fail / Unknown** universally. Do not rename these labels. For skills that use a different rating scheme internally (e.g. High / Medium / Low severity counts), map to the scorecard as follows:

- **Pass** → checks/findings with no issues
- **Partial** → checks/findings with minor or incomplete compliance
- **Fail** → checks/findings with clear violations
- **Unknown** → checks that could not be assessed (static screenshots, SSO-blocked pages, etc.)

### 3. Priority Remediation Matrix — Page Column

When an audit spans multiple pages or flows, add a **Page** column between Priority and Issue:

```html
<thead>
  <tr>
    <th>Priority</th>
    <th>Page</th>
    <th>Issue</th>
    <th>Category</th>
    <th>Severity</th>
    <th>Effort</th>
    <th>Recommended Action</th>
  </tr>
</thead>
```

For single-page audits, omit the Page column.

### 4. Scope & Assumptions — What to Write

| Placeholder          | Content guidance                                                                                                      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `[SCOPE_TEXT]`       | What screens, flows, or features were evaluated. What was explicitly out of scope.                                    |
| `[ASSUMPTIONS_TEXT]` | Any assumptions made due to missing context: user roles assumed, device type assumed, authentication not tested, etc. |

### 5. Confidence & Gaps — What to Write

| Placeholder              | Content guidance                                                                                                                                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `[CONFIDENCE_LEVEL]`     | High / Medium / Low — the overall reliability of findings                                                                                                                                                         |
| `[CONFIDENCE_NARRATIVE]` | 1–2 sentences: e.g. "High — evaluated on live URL with full browser access, contrast ratios measured directly." or "Medium — evaluated from static screenshots; hover and keyboard states could not be verified." |
| `[GAPS_TEXT]`            | List what could not be assessed: "SSO-protected pages not accessible; authenticated user flows not evaluated; mobile viewport not tested." If no gaps, write "No significant gaps identified."                    |

### 6. Executive Summary — Narrative Length

Keep `[EXECUTIVE_SUMMARY_TEXT]` to 3–5 sentences. Include:

1. What was audited and how
2. The most critical finding
3. The overall risk verdict and rationale

### 7. Methodology Cards — Framework Description

`[FRAMEWORK_DESCRIPTION]` should name the specific framework: "Nielsen's 10 Usability Heuristics", "BMW AI Governance Heuristics", "HCI Principles for GenAI Chatbots", etc.

`[EVALUATION_APPROACH]` should describe the input method: "Live URL audited using browser tools (Playwright), accessibility inspector, and console monitoring." or "Evaluated from static screenshots provided by the user."

---

## Adding New Section Types

If a consuming skill needs an additional section beyond the 9 in the contract (e.g. a raw data table, a trend chart), insert it **between** Findings and Priority Remediation Matrix, or **after** Confidence & Gaps. Never insert before the Cover or between Cover and Scope & Assumptions.

Use an existing CSS class for the container (`.section`, `.evidence`, `.executive-summary`) rather than inventing new styles. If a new component style is genuinely required, add it to `report-styles.css` and document it here.
