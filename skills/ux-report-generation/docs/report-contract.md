# Report Contract

This document defines the structural and visual contract that every DesignOps evaluation report must satisfy. All consuming skills must comply with these specifications exactly.

---

## Required Report Sections

Every report must include all of the following sections **in this order**:

| #   | Section                         | Content                                                                                                                |
| --- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| 1   | **Cover**                       | App name, skill/framework used, review date, reviewer, model tested, total checks, overall risk                        |
| 2   | **Scope & Assumptions**         | Audit scope (what is in/out of scope), primary user tasks evaluated, assumptions made where information was incomplete |
| 3   | **Executive Summary**           | Overall risk level, total heuristic/check count, key finding counts, narrative overview                                |
| 4   | **Scorecard**                   | Visual pass / partial / fail / unknown counts                                                                          |
| 5   | **Risk Banner**                 | Overall risk level with icon and description                                                                           |
| 6   | **Findings**                    | Category-by-category cards — structure depends on the parent skill                                                     |
| 7   | **Priority Remediation Matrix** | Table sorted by priority: issue, category, severity, effort, action                                                    |
| 8   | **Methodology**                 | Framework name, evaluation approach, rating scale, severity legend                                                     |
| 9   | **Confidence & Gaps**           | Overall confidence level (High / Medium / Low), evidence quality notes, checks that could not be performed and why     |

Do not reorder sections. Do not omit sections — if content is unavailable for a section, insert a clearly marked placeholder.

### Section 3: Audit Completeness Score (New in v2.3.0)

This section provides transparency about what was checked and explains any gaps. It should appear immediately after the Executive Summary.

**Format:**

```html
<section class="completeness-score">
  <h2>Audit Completeness Score</h2>
  <table>
    <thead>
      <tr>
        <th>Check Category</th>
        <th>Status</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td
          colspan="3"
          style="font-weight: 600; background: var(--color-surface-info);"
        >
          USABILITY (Nielsen Audit)
        </td>
      </tr>
      <tr>
        <td>Contrast ratios</td>
        <td>✅ Complete</td>
        <td>7 elements measured</td>
      </tr>
      <tr>
        <td>Font sizes</td>
        <td>✅ Complete</td>
        <td>All headings checked</td>
      </tr>
      <tr>
        <td>Keyboard navigation</td>
        <td>✅ Complete</td>
        <td>12 tabs documented</td>
      </tr>
      <tr>
        <td>Console errors</td>
        <td>✅ Complete</td>
        <td>14 errors found</td>
      </tr>
      <tr>
        <td>Heading hierarchy</td>
        <td>✅ Complete</td>
        <td>H1-H3 documented</td>
      </tr>
      <tr>
        <td>Full page scroll</td>
        <td>✅ Complete</td>
        <td>No scroll bugs</td>
      </tr>
      <tr>
        <td
          colspan="3"
          style="font-weight: 600; background: var(--color-surface-info);"
        >
          CONTENT (UX Writing Review)
        </td>
      </tr>
      <tr>
        <td>Search placeholder</td>
        <td>✅ Complete</td>
        <td>Documented</td>
      </tr>
      <tr>
        <td>Button labels (min 3)</td>
        <td>✅ Complete</td>
        <td>5 buttons reviewed</td>
      </tr>
      <tr>
        <td>Navigation labels</td>
        <td>✅ Complete</td>
        <td>Documented</td>
      </tr>
      <tr>
        <td>Form elements</td>
        <td>⚠️ N/A</td>
        <td>No forms present</td>
      </tr>
      <tr>
        <td>Link text</td>
        <td>✅ Complete</td>
        <td>7 empty links flagged</td>
      </tr>
      <tr>
        <td>Heading text</td>
        <td>✅ Complete</td>
        <td>H1-H2 reviewed</td>
      </tr>
    </tbody>
  </table>
  <p>
    <strong>Overall Completeness: 95%</strong> (USABILITY: 100%, CONTENT: 90%)
  </p>
  <p>
    <em
      >Note: Form elements marked N/A as no forms were present on audited
      pages.</em
    >
  </p>
</section>
```

**Status Icons:**

- ✅ Complete — check was performed with documented results
- ⚠️ N/A — check not applicable to audited interface
- ❌ Skipped — check was not performed (explain why in Details column)

### Section 4: Mandatory Checks Performed (New in v2.3.0)

This section shows specific results for the baseline accessibility and usability checks that are required for every Nielsen audit. It should appear after the Audit Completeness Score.

**Format:**

```html
<section class="mandatory-checks">
  <h2>Mandatory Checks Performed</h2>

  <div class="check-result">
    <h3>✅ Contrast Ratios</h3>
    <ul>
      <li>
        H1 heading: <strong>1.33:1</strong> against #FFFFFF (bgSource: inherited
        from body) — <span class="fail">FAIL</span> (4.5:1 required)
      </li>
      <li>
        Navigation links: <strong>15.80:1</strong> against #1F2328 —
        <span class="pass">PASS</span>
      </li>
      <li>
        Body text: <strong>8.37:1</strong> against #FFFFFF —
        <span class="pass">PASS</span>
      </li>
    </ul>
  </div>

  <div class="check-result">
    <h3>✅ Font Sizes</h3>
    <ul>
      <li>H1 heading: 11px — <span class="fail">FAIL</span> (12px minimum)</li>
      <li>Body text: 14px — <span class="pass">PASS</span></li>
    </ul>
  </div>

  <div class="check-result">
    <h3>✅ Keyboard Navigation</h3>
    <p><strong>12 Tab stops documented:</strong></p>
    <ol>
      <li>Skip to content link</li>
      <li>BMW logo</li>
      <li>Search input</li>
      <li>Navigation: Dashboard</li>
      <li>Navigation: Catalog</li>
      <!-- ... rest of stops -->
    </ol>
  </div>

  <div class="check-result">
    <h3>✅ Console Errors</h3>
    <p><strong>14 errors found:</strong></p>
    <ul>
      <li>404 GET /api/recent-apps — Network error</li>
      <li>
        Uncaught TypeError: Cannot read properties of undefined — search.js:42
      </li>
      <!-- ... rest of errors -->
    </ul>
  </div>

  <div class="check-result">
    <h3>✅ Heading Hierarchy</h3>
    <pre>
H1: "Welcome back, [User]"
  H2: "Quick Actions"
  H2: "Recent Applications"
  H2: "Popular Templates"
    </pre>
  </div>

  <div class="check-result">
    <h3>✅ Full Page Scroll</h3>
    <p>
      No layout shifts, broken scroll behaviors, or infinite scroll bugs
      detected.
    </p>
  </div>
</section>
```

**Key Requirements:**

- **Contrast ratios** must include `bgSource` (inherited/assumed) for transparency
- **Keyboard navigation** must list minimum 10 Tab stops
- **Console errors** must include actual error messages (not just count)
- Use `<span class="pass">PASS</span>` or `<span class="fail">FAIL</span>` for visual status

---

## Density Design System Tokens

All visual styling **must** use the CSS custom properties below. Do not hardcode any colour, spacing, or typography value.

### Primitive Tokens

```css
/* Red */
--color-red-100: #ffefef;
--color-red-200: #ffd4d4;
--color-red-600: #df001a;
--color-red-700: #aa0014;

/* Green */
--color-green-100: #e5fceb;
--color-green-200: #9ff7b7;
--color-green-600: #2a813f;
--color-green-700: #185f28;

/* Yellow */
--color-yellow-100: #fff7de;
--color-yellow-200: #ffe38e;
--color-yellow-700: #744b00;

/* Blue — informational surfaces */
--color-blue-100: #ecf3ff;
--color-blue-600: #0071c5;
--color-blue-700: #005499;

/* Ocean — action / interactive (Density color-surface-action-strong) */
--color-ocean-100: #e0f2ff;
--color-ocean-600: #037493;
--color-ocean-700: #035970;

/* Grey / Cool Grey */
--color-grey-100: #f5f6f6;
--color-cool-grey-200: #dcdee1;
--color-cool-grey-600: #69707a;
--color-cool-grey-900: #1f2328;
```

### Semantic Surface Tokens

```css
--color-surface-page: var(--color-grey-100);
--color-surface-base: #ffffff;
--color-surface-critical: var(--color-red-100);
--color-surface-positive: var(--color-green-100);
--color-surface-caution: var(--color-yellow-100);
--color-surface-info: var(--color-blue-100);
--color-surface-invert: var(--color-cool-grey-900);
```

### Semantic Border Tokens

```css
--color-border-neutral: var(--color-cool-grey-200);
--color-border-critical: var(--color-red-200);
--color-border-positive: var(--color-green-200);
--color-border-caution: var(--color-yellow-200);
```

### Semantic Typography Tokens

```css
--color-typography-base: var(--color-cool-grey-900);
--color-typography-critical: var(--color-red-700);
--color-typography-positive: var(--color-green-700);
--color-typography-caution: var(--color-yellow-700);
```

### Report Semantic Aliases

Define these aliases in the `:root` block of every generated report:

```css
/* Severity */
--severity-critical: var(--color-red-600);
--severity-high: var(--color-red-600);
--severity-medium: var(--color-yellow-700);
--severity-low: var(--color-green-600);

/* Status */
--status-pass: var(--color-green-700);
--status-partial: var(--color-yellow-700);
--status-fail: var(--color-red-600);
--status-unknown: var(--color-cool-grey-600);

/* Action — use for all interactive / branded elements (Density ocean-600) */
--color-action: var(--color-ocean-600);
```

---

## Status Ratings

| Rating      | CSS class | Meaning                                                  |
| ----------- | --------- | -------------------------------------------------------- |
| **Pass**    | `pass`    | Controls are implemented, tested, and evidenced          |
| **Partial** | `partial` | Controls exist but are incomplete or weakly evidenced    |
| **Fail**    | `fail`    | Required controls are absent or demonstrably ineffective |
| **Unknown** | `unknown` | Insufficient evidence to determine status                |

---

## Severity Levels

| Severity     | CSS class  | Description                              |
| ------------ | ---------- | ---------------------------------------- |
| **Critical** | `critical` | Immediate safety, GDPR, or security risk |
| **High**     | `high`     | Significant UX or trust impact           |
| **Medium**   | `medium`   | Notable usability gap                    |
| **Low**      | `low`      | Minor improvement opportunity            |

---

## Effort Estimates

| Effort | CSS class  | Description                |
| ------ | ---------- | -------------------------- |
| **S**  | `effort-s` | Small — less than 1 sprint |
| **M**  | `effort-m` | Medium — 1–2 sprints       |
| **L**  | `effort-l` | Large — 3+ sprints         |

---

## Priority Tiers (Remediation Matrix)

| Priority | CSS class | Meaning                                        |
| -------- | --------- | ---------------------------------------------- |
| **P0**   | `p0`      | Critical + immediate — fix before next release |
| **P1**   | `p1`      | High — fix within current sprint               |
| **P2**   | `p2`      | Medium — schedule for next sprint              |
| **P3**   | `p3`      | Low — backlog item                             |

### Assigning Priority

Derive priority from the combination of severity and current risk:

| Severity | → Priority |
| -------- | ---------- |
| Critical | P0         |
| High     | P1         |
| Medium   | P2         |
| Low      | P3         |

Override to a higher priority tier when the finding directly blocks a release, affects GDPR compliance, or causes a complete feature failure.

---

## Finding Card Structure

Every finding must contain these elements in order:

1. **Finding header** — title, status badge, severity badge, effort badge
2. **Description** — 1–3 sentences explaining the issue
3. **Evidence block** — specific, observed evidence (what was seen and where)
4. **Screenshot block** — embedded screenshot (or placeholder if unavailable)
5. **Recommendation block** — concrete, actionable fix

See `templates/report-shell.html` for the exact HTML markup pattern.
