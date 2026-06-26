---
name: ux-reviewer
description: Comprehensive UX review combining Nielsen heuristic evaluation with interface copy assessment. Use when user asks for a complete UX review, holistic usability evaluation, combined audit and content review, or wants both usability findings and copy recommendations. Also use when user mentions "full UX review", "review my interface", "check usability and copy", or wants integrated UX and content design feedback.
license: Proprietary
compatibility: Works with text descriptions, screenshots, live URLs, prototypes, and design files. Requires browser access for optimal results.
metadata:
  authors:
    - Adele Campbell <adele.campbell@bmwithub.co.za>
    - Heinrich Mostert <heinrich.mostert@bmwithub.co.za>
  version: "1.4.0"
  tags:
    - ux-review
    - usability
    - content-design
    - nielsen-heuristics
    - ux-writing
    - comprehensive-audit
---

# ux-reviewer

## Goal

Deliver a comprehensive UX review that evaluates both usability (via Nielsen heuristics) and interface content quality (via UX writing best practices), producing an integrated assessment with prioritized recommendations.

## When to Use This Skill

Use **ux-reviewer** when:

- User requests a "complete UX review" or "holistic usability evaluation"
- Both interaction design AND content/copy need assessment
- User wants integrated findings across usability and content quality
- Project requires coordinated UX and content design improvements

## Inputs

Gather as many of these as available:

**Context:**

- Product/feature description and user goals
- Target audience and use cases
- Platform (web/mobile/desktop)
- Brand voice and tone requirements (especially Density guidelines)

**Artifacts:**

- Screenshots or image files (PNG/JPG/WebP — analysed via vision, see Phase 1.5)
- Image URLs (publicly accessible — passed directly to `gpt-4o`)
- Figma links (use `figma-implement-design` skill to export screens first)
- Live application URL (preferred for thorough evaluation)
- User flows or journey maps
- Existing copy guidelines or voice/tone documentation

**Scope:**

- Specific pages/screens to review
- Priority areas or known pain points
- Business goals and success metrics

If inputs are incomplete, ask clarifying questions before proceeding.

## Outputs

A comprehensive UX review report containing:

1. **Executive Summary** - Key findings and high-priority recommendations
2. **Nielsen Heuristic Audit Findings** - Structured usability issues with severity ratings
3. **Content & Copy Assessment** - Interface text evaluation and improvement recommendations
4. **Integrated Recommendations** - Prioritized action plan combining both perspectives
5. **Optional:** Combined HTML report with both usability and content findings

## Workflow

### Phase 1: Gather Context and Define Scope

1. **Collect inputs** listed above
2. **Clarify scope boundaries:**
   - What pages/flows are in scope?
   - Are there known problem areas to prioritize?
   - What's the timeline and effort budget?
3. **Identify constraints:**
   - Technical limitations
   - Brand/legal requirements
4. **Confirm deliverable format:**
   - Separate reports or combined document?
   - Need for presentation slides or executive summary?

### Phase 1.5: Vision Analysis (when screenshots/images are provided)

**Trigger:** User provides image file paths, base64 data, or image URLs instead
of (or in addition to) a live URL.

**Goal:** Extract a structured textual description of the UI that feeds into
the standard Nielsen + copy audit workflow. Vision analysis cannot replace
live browser testing (no hover states, no console errors, no DOM inspection)
but captures layout, text, components, and visual hierarchy accurately.

**Module — import and call:**

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/ux-reviewer"))
from analyse_ui_screenshot import analyse_ui_screenshot, compare_screenshots, UXScreenAnalysis

# Single screenshot (file path, URL, or base64 data URL):
analysis = analyse_ui_screenshot("path/to/screenshot.png", context="Dashboard home screen")
print(analysis.layout_description)   # typed str — no dict key access
print(analysis.visible_text)         # typed List[str]
print(analysis.potential_issues)     # typed List[str]

# Multiple screens (before/after or desktop vs mobile):
analysis = compare_screenshots(["before.png", "after.png"], context="Login redesign")
```

Module: `~/.opencode/skills/ux-reviewer/analyse_ui_screenshot.py`
Functions: `analyse_ui_screenshot(image_source, context="")`, `compare_screenshots(image_sources, context="")`
Model: `gpt-4o` (vision). Returns `UXScreenAnalysis` — typed Pydantic model, no JSON parsing needed.

**How vision analysis maps to the audit phases:**

| `UXScreenAnalysis` field | Used in |
|---|---|
| `.layout_description` + `.visual_hierarchy` | Phase 2: Nielsen H4 (consistency), H8 (aesthetic), H6 (recognition) |
| `.visible_text` | Phase 3: full content inventory — all UI copy |
| `.components` | Phase 2: interaction design, design system compliance |
| `.potential_issues` | Phase 2: initial findings seeds — verify and rate severity |

**Limitations to note in the report:**
- Dynamic states (hover, loading, error) cannot be observed from a static screenshot
- Console errors and DOM structure are not accessible — note as "Unable to test — requires live browser"
- Vision tokens are higher-cost than text — limit to the screens in scope
- Max image size: 20 MB per image; resize large screenshots before sending

**Multiple images / comparison:**

Pass multiple images in a single request to compare screens (e.g. before/after, desktop vs mobile):

```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path.home() / ".opencode/skills/ux-reviewer"))
from analyse_ui_screenshot import compare_screenshots

analysis = compare_screenshots(["screen1.png", "screen2.png"])
print(analysis.potential_issues)   # typed List[str] — no JSON parsing needed
```

---

### Phase 2: Conduct Nielsen Heuristic Audit

Follow the Nielsen heuristic audit workflow completely:

1. Define scope and risk context
2. Use browser dev tools for analysis (if URL available):

   - Element inspector for layout and design
   - Network tab for performance issues

3. **DOM Structure Inspection (MANDATORY):**

   - [ ] Check for duplicate elements (same content appearing multiple times in DOM)
   - [ ] Identify all sticky/fixed positioned elements (position: sticky, position: fixed)
   - [ ] Count total sticky elements (flag if 3+)
   - [ ] Document z-index conflicts or overlap risks
   - [ ] Note any unnecessary wrapper divs or structural bloat

4. Evaluate all 10 Nielsen heuristics systematically
5. Perform systematic analysis across:
   - Visual design & layout
   - Interaction design
   - Design system compliance
   - Information architecture
6. Apply severity ratings (0-4 scale)
7. Validate comprehensive issue coverage

**Capture all findings** in structured format for integration later.

### Phase 2.5: Validate Nielsen Audit Completion (BLOCKING CHECKPOINT)

**🚨 CRITICAL: Before proceeding to Phase 3, verify the Nielsen audit is complete.**

- [ ] ✅ All 10 Nielsen heuristics evaluated (see `nielsen-heuristics-checklist.md`)
- [ ] ✅ DOM structure checks complete (duplicates, sticky elements, z-index)
- [ ] ✅ Interactive behavior tests complete (Phase 2.7)

**If ANY check is incomplete, STOP and return to Phase 2.**

---

### Phase 2.7: Interactive Behavior & Spatial Design Testing (MANDATORY)

**🎯 OBJECTIVE:** Test dynamic interactions and spatial relationships that static inspection misses.

**Testing checklist:**

**1. Page-Level Orientation (H2):**

- [ ] Page has descriptive introduction/overview (not just title)
- [ ] First-time users can understand page purpose
- [ ] Explanatory text present near H1

**2. Spatial Relationships (H4, H6):**

- [ ] Help buttons positioned next to fields they explain
- [ ] Filter controls grouped together visually
- [ ] Related actions (Save/Cancel) placed together

**3. Interactive States (H1, H6):**

- [ ] Multi-select dropdowns show selected values when closed
- [ ] Hover states provide visual feedback
- [ ] Selected states show confirmation

**4. Dynamic Search Features (H7, H5):**

- [ ] Autocomplete suggests options as user types
- [ ] Type-ahead filters suggestions
- [ ] Predictive text or "Did you mean..." for typos
- [ ] Live filtering (if applicable)

**If live interaction unavailable:** Note "Unable to test [feature] - requires live browser" and recommend the feature.

**Validation:**

- [ ] All 4 categories tested or documented as untestable

---

### Phase 3: Assess Interface Copy and Content

**Reference:** `references/ux-writing-evaluation-guide.md` — Comprehensive guide with:

- 5 core UX writing principles (Clarity, Conciseness, Helpfulness, Consistency, Voice & Tone)
- Content inventory checklist (search, buttons, forms, errors, links, headings, empty states)
- Common anti-patterns (placeholder as label, generic buttons, vague errors, non-descriptive links)
- Density voice & tone guidelines for BMW applications
- Finding template for content issues

Review all interface text through the UX writing lens:

**MANDATORY Content Inventory (refer to `ux-writing-evaluation-guide.md`):**

- [ ] Search functionality (placeholder, button label)
- [ ] Primary CTAs (minimum 3 buttons — flag generic labels)
- [ ] Navigation labels (descriptive vs. vague)
- [ ] Help & Documentation (visible link/button location)
- [ ] Form elements (labels, placeholders, helper text, errors)
- [ ] Link text (flag empty or "Click here")
- [ ] Headings (H1, H2 text)

**Evaluate against 5 UX writing principles:**

- Clarity, Conciseness, Helpfulness, Consistency, Voice & Tone

**Density compliance** (BMW apps): Reference `density-*.md` files

**Content Check Validation:**

- [ ] All 7 mandatory items documented or noted as N/A
- [ ] Content issues documented with recommendations
- [ ] Findings linked to Nielsen heuristics (see `content-to-heuristic-mapping.md`)

---

### Phase 4: Integrate and Prioritize Findings

**Reference documentation:**

- `references/integrated-evaluation-guide.md` — Complete workflow for combining usability + content findings
- `references/content-to-heuristic-mapping.md` — Maps content issues to Nielsen heuristics
- `references/integrated-finding-templates.md` — Ready-to-use templates for writing integrated findings

Synthesize findings from both perspectives:

1. **Identify overlapping issues:**

   - Usability issues with content components (e.g., unclear button labels)
   - Content issues that violate heuristics (e.g., vague error messages = poor error prevention)
   - **Merge duplicates** — Don't list the same issue twice from different perspectives

2. **Cross-reference findings:**

   - Link content issues to relevant Nielsen heuristics (see `content-to-heuristic-mapping.md`)
   - Note where content improvements could resolve usability problems
   - Map severity based on heuristic impact (H9 errors = HIGH, H7 efficiency = LOW)

3. **Create unified priority matrix:**

   | Priority     | Criteria                                          | Examples                                        |
   | ------------ | ------------------------------------------------- | ----------------------------------------------- |
   | **Critical** | Severity 4 usability issues + content blockers    | Misleading error messages, unclear primary CTAs |
   | **High**     | Severity 3 usability + important content gaps     | Inconsistent terminology, missing helper text   |
   | **Medium**   | Severity 2 usability + content consistency issues | Minor copy improvements, label refinements      |
   | **Low**      | Severity 1 cosmetic + optional enhancements       | Polish, voice/tone fine-tuning                  |

4. **Group by effort and impact:**

   - **Quick wins** - High impact, low effort (both usability + content)
   - **Planned improvements** - Medium effort, meaningful impact
   - **Strategic work** - High effort, systemic changes

5. **Use finding templates:**
   - Reference `integrated-finding-templates.md` for standard formats
   - Each finding should include: Issue, Heuristic, Content Problem, Usability Impact, Severity, Recommendation, Rationale

### Phase 5: Generate Integrated Report

**Load and execute:** `ux-report-generation` skill

Create a comprehensive report that presents both usability and content findings cohesively:

1. **Executive Summary**

   - Overall assessment (score/rating if applicable)
   - Top 3-5 critical issues
   - Key recommendations by priority tier

2. **Audit Completeness Score** (Mandatory Section)

   Document audit depth and transparency:

   ```markdown
   ## Audit Completeness Score

   | Check Category                           | Status      | Details               |
   | ---------------------------------------- | ----------- | --------------------- |
   | **USABILITY (Nielsen Audit)**            |             |                       |
   | Visibility of system status              | ✅ Complete | Evaluated             |
   | Match between system and real world      | ✅ Complete | Evaluated             |
   | User control and freedom                 | ✅ Complete | Evaluated             |
   | Consistency and standards                | ✅ Complete | Evaluated             |
   | Error prevention                         | ✅ Complete | Evaluated             |
   | Recognition rather than recall           | ✅ Complete | Evaluated             |
   | Flexibility and efficiency               | ✅ Complete | Evaluated             |
   | Aesthetic and minimalist design          | ✅ Complete | Evaluated             |
   | Help users recognize/recover from errors | ✅ Complete | Evaluated             |
   | Help and documentation                   | ✅ Complete | Evaluated             |
   | **CONTENT (UX Writing Review)**          |             |                       |
   | Search placeholder                       | ✅ Complete | Documented            |
   | Button labels (min 3)                    | ✅ Complete | 5 buttons reviewed    |
   | Navigation labels                        | ✅ Complete | Documented            |
   | Form elements                            | ⚠️ N/A      | No forms present      |
   | Link text                                | ✅ Complete | 7 empty links flagged |
   | Heading text                             | ✅ Complete | H1-H2 reviewed        |

   **Overall Completeness: 100%**
   (USABILITY: 100%, CONTENT: 90%)

   _Note: Form elements marked N/A as no forms were present on audited pages._
   ```

   This section provides transparency about what was checked and explains any gaps.

3. **Nielsen Heuristic Findings**

   - Standard Nielsen audit table with all findings
   - Include content-related usability issues here

4. **Content & Copy Assessment**

   - Interface text inventory
   - Content quality findings by touchpoint type
   - Density voice/tone compliance (if applicable)
   - Recommended copy changes

5. **Integrated Recommendations**

   - Combined priority matrix
   - Quick wins list (both usability + content)
   - Planned improvements roadmap
   - Strategic initiatives

6. **Appendices** (optional)
   - Detailed copy recommendations
   - Before/after examples
   - Design system compliance notes

**Report generation:**

Follow `ux-report-generation` skill guidelines:

- Save to: `reports/ux-reviewer/`
- Filename: `<app-name>-ux-review-report.html`
- Include both usability and content findings
- Use Density styling and tokens
- Generate PDF: `<app-name>-ux-review-report.pdf`

### Phase 6: Deliver Results and Next Steps

1. **Present findings:**

   - Share HTML report (and PDF if generated)
   - Highlight critical issues requiring immediate attention
   - Emphasize quick wins for early momentum

2. **Provide implementation guidance:**

   - Suggest sequencing (what to fix first)
   - Note dependencies between fixes
   - Estimate effort for major initiatives

3. **Offer follow-up support:**
   - Available for specific copy writing tasks
   - Can conduct focused audits on updated designs
   - Ready to validate fixes against findings

## Integration Points

This skill integrates usability evaluation and content assessment:

- **`ux-report-generation`** - Load when creating the final integrated report

Reference documentation is loaded as needed during execution.

### Reference Documentation

All reference files are in `references/` directory.

**Integration & Workflow:**

- `integrated-evaluation-guide.md` — Complete workflow for combining usability + content
- `content-to-heuristic-mapping.md` — Maps content issues to Nielsen heuristics
- `integrated-finding-templates.md` — 9 ready-to-use finding templates

**UX Writing & Content:**

- `ux-writing-evaluation-guide.md` — Evaluation methodology (6 principles, inventory checklist)
- `copy-patterns.md` — Ready-to-use UI copy templates by component

**BMW Density (6 files):**

- `density-voice-and-tone.md` — BMW voice characteristics
- `density-action-labels.md` — 50+ BMW-approved labels (English/German)
- `density-error-messages.md` — BMW error principles
- `density-numerics.md` — Date/time/number/currency formatting
- `density-text.md` — Spelling, capitalization, punctuation
- `density-imprint.md` — Legal footer requirements

**Nielsen:**

- `nielsen-heuristics-checklist.md` — Complete 10 heuristics reference

**Usage:**

- Phase 2: Use Nielsen checklist
- Phase 3: Start with evaluation guide, reference patterns + Density files
- Phase 4: Follow integration guide, use finding templates

## Examples

### Example 1: E-commerce Checkout Review

**Input:** "Review our checkout flow for usability and copy quality"

**Process:**

1. Conduct Nielsen heuristic audit → identify usability issues (form validation, error prevention, progress indicators)
2. Assess interface copy → evaluate checkout copy (CTAs, error messages, form labels, confirmation text)
3. Integrate findings → note that unclear error messages are both usability AND content issues
4. Generate report → prioritize fixes (critical: misleading "Submit" button + vague error text)

### Example 2: Dashboard UX Audit

**Input:** Live URL + "Complete UX review of admin dashboard"

**Process:**

1. Open browser, load dashboard
2. Conduct Nielsen audit → find unclear icons, missing feedback, inconsistent patterns
3. Review all dashboard copy → tooltips vague, empty states unhelpful, action labels inconsistent
4. Identify quick wins → improve tooltip copy, standardize action labels (overlapping fixes)
5. Generate combined report with priority matrix

## Quality Standards

A comprehensive UX review should:

- **Nielsen audit:** 15-25 usability findings across diverse categories (following mandatory checks)
- **Content assessment:** Review ALL interface text touchpoints
- **Integration:** Clearly identify where usability and content issues overlap
- **Actionability:** Specific, implementable recommendations for both usability and content
- **Prioritization:** Clear quick wins, medium-term improvements, and strategic initiatives

## Guardrails

- **Always perform both evaluations** - Never skip either the usability audit or content assessment
- **Execute mandatory checks** - Hover states, console errors, DOM structure inspection
- **Don't duplicate findings** - If an issue touches both usability and content, present it once with both perspectives noted
- **Maintain separate perspectives** - Keep usability findings distinct from pure content/copy issues in the report
- **Follow report standards** - Use ux-report-generation skill for consistent output formatting
- **Be comprehensive but concise** - Integrate findings without creating overwhelming documentation
