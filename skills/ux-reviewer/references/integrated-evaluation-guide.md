# Integrated UX Evaluation Guide

## Purpose

This guide explains how to conduct a comprehensive UX review that evaluates both **usability** (Nielsen heuristics) and **interface content quality** (UX writing), then integrates findings into a unified assessment.

---

## When to Use Combined Evaluation

Use the **ux-reviewer** skill (combined approach) when:

✅ **Both usability AND content need assessment** — You want to catch interaction design issues AND improve interface copy
✅ **Holistic product evaluation** — Stakeholders need a complete picture of UX quality
✅ **Coordinated improvements** — Fixes should address both usability and content simultaneously
✅ **Launch readiness reviews** — Full quality check before shipping

❌ **Don't use combined approach** when only one aspect is needed:

- **Usability-only** → Use `nielsen-heuristics-ux-audit` directly
- **Copy-only** → Use `ux-writing` directly

---

## Evaluation Workflow

### Phase 1: Nielsen Heuristic Audit (Usability)

**Follow the complete nielsen-heuristics-ux-audit workflow:**

1. **Scope definition** — Which pages/flows to evaluate
2. **Systematic evaluation** — All 10 Nielsen heuristics
3. **DOM structure inspection** — Duplicates, sticky elements, z-index hierarchy
4. **Phase 2.7 interactive testing** — Page context, spatial grouping, interactive states, dynamic search
5. **Severity ratings** — 0-4 scale (catastrophic to cosmetic)
6. **Finding documentation** — Structured format with screenshots

**Deliverable:** Complete list of usability findings with severity levels

---

### Phase 2: UX Writing Assessment (Content)

**Follow the complete ux-writing workflow:**

1. **Content inventory** — Catalog all interface text:

   - Search placeholders and labels
   - Button labels (minimum 3 CTAs)
   - Navigation labels
   - Form elements and helpers
   - Error/success messages
   - Link text
   - Headings (H1-H3)

2. **Evaluate against principles:**

   - **Clarity** — Is meaning immediately clear?
   - **Conciseness** — Any unnecessary words?
   - **Helpfulness** — Does it guide users toward success?
   - **Consistency** — Same terms used consistently?
   - **Voice & tone** — Matches brand guidelines?

3. **Density compliance checks** (when applicable):
   - Reference density-voice-and-tone.md
   - Reference density-action-labels.md
   - Reference density-error-messages.md

**Deliverable:** Complete list of content findings with recommendations

---

### Phase 3: Integration & Cross-Reference

This is where the **magic happens** — finding connections between usability and content issues.

#### Step 1: Identify Overlapping Issues

Ask yourself: **Does this content issue also violate a Nielsen heuristic?**

**Examples of overlap:**

| Content Issue                                   | Overlapping Heuristic                        | Combined Finding                                                    |
| ----------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------- |
| Vague error message "Error occurred"            | H9: Help users recognize/recover from errors | Error message doesn't explain what went wrong or how to fix it      |
| Button labeled "Submit" (generic)               | H6: Recognition rather than recall           | Button doesn't indicate what will be submitted or what happens next |
| Inconsistent terminology ("Delete" vs "Remove") | H4: Consistency and standards                | Inconsistent action labels create confusion about system behavior   |
| Missing field labels                            | H6: Recognition                              | Users can't identify form fields without visible labels             |
| Truncated dropdown text "BMW ..."               | H4: Consistency + H6: Recognition            | Users can't see current selection — violates visibility principle   |

**Integration Tip:** Content issues often **manifest** usability problems. A vague error message IS a usability violation (H9). Treating them as separate findings creates duplication.

#### Step 2: Consolidate Duplicate Findings

If a finding appears in both audits, **merge them** into a single integrated finding:

**Before (Separate):**

- **Nielsen Finding:** Dropdown shows "BMW ..." truncated text (H4 violation)
- **Content Finding:** Dropdown label unclear due to truncation

**After (Integrated):**

- **Integrated Finding:** Dropdown displays truncated text "BMW ..." instead of "BMW Group Internal" — violates consistency heuristic (H4) and prevents users from recognizing current selection (H6). This content truncation creates a functional usability problem.

#### Step 3: Map Content Issues to Heuristics

For content-only findings, **link them to relevant heuristics** to show their usability impact:

| Content Finding                              | Primary Heuristic    | Explanation                                                  |
| -------------------------------------------- | -------------------- | ------------------------------------------------------------ |
| Placeholder used as label                    | H6: Recognition      | Placeholders disappear on focus — users forget field purpose |
| Search placeholder "Type ''/'' to search"    | H2: Match real world | Non-standard instruction increases cognitive load            |
| "This step is not relevant" (no explanation) | H9: Error recovery   | Message doesn't help user understand why or what to do next  |
| Missing page introduction                    | H2: Match real world | First-time users lack orientation context                    |
| Button "Create step" too terse               | H6: Recognition      | Could be "Create new onboarding step" for clarity            |

**Why this matters:** Linking content to heuristics demonstrates that **good copy is part of good UX**, not a separate cosmetic concern.

---

### Phase 4: Prioritization Matrix

Create a **unified priority matrix** that considers both severity (Nielsen) and content impact:

#### Priority Levels

| Priority     | Criteria                                        | Examples                                                                                       |
| ------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **CRITICAL** | Severity 4 (catastrophic) + content blockers    | Misleading error messages that cause data loss; Primary CTA missing or unclear                 |
| **HIGH**     | Severity 3 (major) + important content gaps     | Vague error messages; Unclear button labels for primary actions; Missing required field labels |
| **MEDIUM**   | Severity 2 (moderate) + content inconsistencies | Inconsistent terminology; Minor label improvements; Missing helper text                        |
| **LOW**      | Severity 1 (minor) + optional enhancements      | Voice/tone refinements; Optional microcopy improvements; Copy polish                           |

#### Impact-Effort Matrix

Group findings by **effort vs. impact** for actionable recommendations:

```
HIGH IMPACT
│
│  PLAN CAREFULLY        QUICK WINS ⭐
│  (High effort)         (Low effort)
│  • Major redesigns     • Fix dropdown truncation
│  • Feature additions   • Rewrite error messages
│                        • Improve button labels
│
│  DEPRIORITIZE          PLANNED IMPROVEMENTS
│  (Nice-to-have)        (Worth doing)
│  • Polish only         • Add page introductions
│  • Optional features   • Improve button labels
│
└─────────────────────────────────────► LOW EFFORT
```

**Quick Wins** should combine:

- High usability impact (severity 3-4)
- Simple content fixes (word/phrase changes)
- Low implementation effort (no major redesign)

---

### Phase 5: Integrated Report

Generate a **single comprehensive report** that presents findings cohesively:

#### Report Structure

1. **Executive Summary**

   - Overall UX score/assessment
   - Top 3-5 critical issues (combined usability + content)
   - Key recommendations by priority tier

2. **Audit Completeness Score**

   - Nielsen heuristics checked (10/10)
   - Content categories evaluated (7/7)
   - Phase 2.7 interactive tests performed (4/4)

3. **Integrated Findings Table**

   - Single table with all findings
   - Columns: Issue, Heuristic, Content Impact, Severity, Priority
   - Merged duplicates shown as single row

4. **Nielsen Heuristic Findings (Detailed)**

   - Traditional Nielsen audit table
   - Include content-related usability issues

5. **Content & Copy Assessment (Detailed)**

   - Interface text inventory
   - Content quality findings by type
   - Density compliance notes

6. **Integrated Recommendations**
   - Combined priority matrix (Impact × Effort)
   - Quick wins list (both usability + content)
   - Planned improvements roadmap

---

## Common Pitfalls to Avoid

❌ **Double-counting issues** — Don't list "vague error message" as both a Nielsen finding AND a content finding. Merge them.

❌ **Treating content as cosmetic** — Map content issues to heuristics to show their usability impact.

❌ **Separate reports** — Generate ONE integrated report, not two separate documents.

❌ **Ignoring dependencies** — Some fixes require coordination (e.g., redesigning error UI + rewriting error copy).

❌ **Missing cross-references** — Always note when a content issue causes a heuristic violation.

---

## Quality Checklist

Before finalizing your integrated UX review, verify:

- [ ] All overlapping findings **merged** (not duplicated)
- [ ] Content issues **linked** to relevant Nielsen heuristics
- [ ] Priority matrix considers **both** severity and content impact
- [ ] Quick wins identified (high impact, low effort)
- [ ] Report presents **unified** findings (not separate lists)
- [ ] Recommendations address **coordinated** improvements
- [ ] Examples show content + usability working together
- [ ] Severity ratings consistent across integrated findings

---

## Example: Integrated Finding

**❌ Poor (Separated):**

**Usability Finding:**

- Issue: Error message not helpful
- Heuristic: H9
- Severity: HIGH

**Content Finding:**

- Issue: Error says "Error occurred"
- Recommendation: Be more specific

**✅ Good (Integrated):**

**Integrated Finding:**

- **Issue:** Error message "Error occurred" is vague and doesn't help users recover
- **Heuristic:** H9 (Help users recognize, diagnose, and recover from errors)
- **Content Problem:** Generic error text provides no context about what went wrong
- **Usability Impact:** Users can't diagnose root cause or take corrective action
- **Severity:** HIGH (major usability + critical content gap)
- **Recommendation:**
  - **Before:** "Error occurred"
  - **After:** "Unable to save changes. Check your internet connection and try again. [Retry]"
- **Impact:** Users understand the problem and know how to fix it
- **Rationale:** Combines clear explanation (content) with actionable recovery path (usability)

---

## Summary

The **ux-reviewer** workflow integrates Nielsen heuristics and UX writing into a **single cohesive evaluation**. The key is recognizing that **content quality directly impacts usability** — vague copy isn't just poor writing, it's a violation of recognition, error prevention, and help heuristics. By merging findings and prioritizing holistically, you deliver actionable recommendations that improve both interaction design and interface language simultaneously.
