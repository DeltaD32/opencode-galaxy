# UX Writing Evaluation Guide

## Purpose

This guide explains **how to evaluate** interface copy and content during a comprehensive UX review. Use this during **Phase 3 (Content Assessment)** of the ux-reviewer workflow.

**For ready-to-use copy templates and examples,** see [`copy-patterns.md`](copy-patterns.md) — a comprehensive pattern library organized by UI component type (buttons, errors, forms, empty states, etc.).

This guide focuses on **evaluation methodology**: principles, checklists, and common anti-patterns to flag during audits.

---

## Core UX Writing Principles

Every piece of interface text should be evaluated against these 6 principles:

### 1. Clarity

**"Is the meaning immediately clear?"**

**Good copy:**

- Uses simple, everyday words
- Avoids ambiguity
- One clear meaning, not multiple interpretations
- Front-loads important information

**Examples:**

- ❌ "Utilize the interface to commence operations"
- ✅ "Click 'Start' to begin"
- ❌ "Your request has been received"
- ✅ "We received your request. You'll hear from us within 24 hours."

**Tests:**

- Can a 12-year-old understand it?
- Would non-native speakers understand it?
- Is there only ONE way to interpret this?

---

### 2. Conciseness

**"Any unnecessary words?"**

**Good copy:**

- Gets to the point quickly
- Removes filler words and redundancy
- Respects user's time and attention
- Every word earns its place

**Examples:**

- ❌ "In order to proceed, please click the button below"
- ✅ "Click 'Continue' to proceed"
- ❌ "It is important to note that your password must contain at least 8 characters"
- ✅ "Password must be 8+ characters"

**Tests:**

- Can you remove ANY word without losing meaning?
- Are you saying the same thing twice?
- Is this the shortest clear way to say it?

**Word budget guidelines:**

- Button labels: 1-3 words
- Input placeholders: 2-4 words
- Helper text: 5-10 words
- Error messages: 10-20 words
- Empty states: 15-30 words

---

### 3. Helpfulness

**"Does it guide users toward success?"**

**Good copy:**

- Anticipates user questions
- Provides next steps
- Explains "why" when constraints exist
- Suggests alternatives when something isn't available

**Examples:**

- ❌ "Invalid format"
- ✅ "Email must include @ symbol. Example: name@company.com"
- ❌ "Feature unavailable"
- ✅ "This feature is only for premium users. [Upgrade now] or [View free alternatives]"

**Tests:**

- Does this answer "what do I do next?"
- Does this explain "why" for constraints?
- Does this help users recover from errors?
- Does this reduce support ticket volume?

---

### 4. Consistency

**"Same terms used consistently?"**

**Good copy:**

- Uses the same word for the same action throughout
- Maintains consistent tone (formal vs. casual)
- Follows established terminology patterns
- Aligns with platform conventions

**Examples:**

- ❌ "Delete" in one place, "Remove" in another, "Trash" in a third
- ✅ Always use "Delete" for permanent removal, "Remove" for list items
- ❌ Mixed voice: "You can edit" + "The user should save"
- ✅ Consistent voice: Always "you" or always "user," never mixed

**Common inconsistencies to flag:**

- Delete / Remove / Trash / Discard
- Cancel / Close / Exit / Dismiss
- Save / Submit / Confirm / Apply
- Sign in / Log in / Login
- Setting / Settings / Preferences / Options

**Tests:**

- Search for synonyms — are different words used for same action?
- Does tone shift from formal to casual mid-flow?
- Do button labels follow consistent patterns?

---

### 5. Voice & Tone

**"Matches brand guidelines?"**

**Voice** = Consistent personality (friendly, professional, technical)
**Tone** = Emotional context (celebratory for success, apologetic for errors)

**Good copy:**

- Maintains consistent voice throughout product
- Adjusts tone based on context (serious for errors, upbeat for success)
- Matches user expectations for the domain
- Follows brand voice guidelines (e.g., Density voice for BMW)

**Examples:**

| Context     | ❌ Generic          | ✅ BMW Density Voice                                                    |
| ----------- | ------------------- | ----------------------------------------------------------------------- |
| Success     | "Great job!"        | "Changes saved successfully"                                            |
| Error       | "Oops!"             | "Unable to save. Check your connection and try again."                  |
| Empty state | "Nothing here yet!" | "No resources found. Adjust your filters or search for specific tools." |

**Tone guidelines by context:**

| Context     | Tone                    | Example                                                      |
| ----------- | ----------------------- | ------------------------------------------------------------ |
| Success     | Confident, brief        | "Profile updated"                                            |
| Error       | Helpful, apologetic     | "We couldn't load your data. Try refreshing the page."       |
| Warning     | Informative, clear      | "Unsaved changes will be lost. Continue?"                    |
| Empty state | Encouraging, actionable | "No projects yet. Create your first project to get started." |
| Loading     | Patient, specific       | "Loading your dashboard... This may take a few seconds."     |

---

## Content Inventory Checklist

During Phase 3 of ux-reviewer, document ALL of these interface text elements:

### 1. Search & Filtering (MANDATORY)

- [ ] **Search input placeholder** — Document exact text
- [ ] **Search button label** — If visible
- [ ] **Filter labels** — All filter/dropdown labels
- [ ] **"No results" message** — If testable

**Common issues:**

- Placeholders used as labels (disappear on focus)
- Generic placeholders: "Search" → "Search by name, category, or status"
- Instructions as placeholders: "Type ''/'' to search" (confusing)

---

### 2. Primary Actions (MANDATORY — minimum 3)

- [ ] **Primary CTA buttons** — Document at least 3
- [ ] **Secondary action buttons** as anti-pattern
- Verb + noun pattern? ("Save changes" not just "Save") → Good
- Consistent action verbs? ("Delete" everywhere or "Remove" everywhere?)

**Flag these anti-patterns:**

- ❌ Generic labels: "Submit", "OK", "Go", "Click here"
- ❌ Missing verb+noun pattern: "Save" instead of "Save changes"
- ❌ Inconsistent terminology across similar actions

👉 **See [`copy-patterns.md` → Buttons and CTAs](copy-patterns.md#buttons-and-ctas)** for detailed patterns and BMW Density action labels

- ❌ "Submit" (submit what?)
- ❌ "OK" (okay to what?)
- ❌ "Go" (go where?)
- ❌ "Click here" (not descriptive)

---

### 3. Navigation (MANDATORY)

- [ ] **Main navigation labels** — All top-level items
- [ ] **Breadcrumb text** — If present
- [ ] **Tab labels** — If present

**Evaluation:**

- Descriptive vs. vague? ("Dev Resources" vs "Resources")
- Parallel structure? (All nouns or all verbs, not mixed)
- Length consistency? (All 1-2 words or vary widely?)

---

### 4. Forms (if present)

- [ ] **Input labels** — All visible labels
- [ ] **Placeholder text** — All placeholders
- [ ] **Helper text** — Instructions/hints below fields
- [ ] **Required field indicators** — "Required" or asterisk
- [ ] **Validation rules** — Shown proactively or only on error?

**Evaluation:**

- Labels vs. placeholders? Labels should be separate, not only placeholder
- Helper text helpful? Explains format, limits, or why field is needed?
- Required fields clear? Don't rely on color alone (asterisk + "Required" text)

**Good patterns:**

- Visible labels paired with concise helper text where needed
- Required fields clearly indicated with text, not color alone

**Flag when:**

- Placeholder used as label (disappears when typing)
- No helper text for complex fields (date format, password requirements)
- Required fields marked only with color (not accessible)

👉 **See [`copy-patterns.md` → Form Fields](copy-patterns.md#form-fields)** for complete patterns with HTML examples

- [ ] **Error messages** — All visible errors
- [ ] **Success confirmations** — All success messages
- [ ] **Warning messages** — All warnings
- [ ] **Info messages** — Contextual info banners

**Evaluation (use template):**

| Message Type | Current Text     | Has Explanation?  | Has Action? | Recommendation                                                 |
| ------------ | ---------------- | ----------------- | ----------- | -------------------------------------------------------------- |
| Error        | "Error occurred" | ❌ No             | ❌ No       | "Unable to save. Check your connection and try again. [Retry]" |
| Success      | "Saved"          | ✅ Yes (implicit) | ❌ No       | "Changes saved at 3:42 PM"                                     |

**Error message requirements:**

1. **What went wrong** — Specific problem description
2. **Why it happened** — Root cause (optional but helpful)
3. **How to fix** — Actionable next steps
4. **Recovery action** — Button or link to retry/resolve

**Flag these anti-patterns:**

- ❌ Vague: "Error occurred", "Something went wrong", "Invalid input"
- ❌ No recovery action: Error with no "Retry" or "Try again" option
- ❌ Technical jargon: "Error 500", "HTTP timeout", "Null pointer exception"

👉 **See [`copy-patterns.md` → Error Messages](copy-patterns.md#error-messages)** for templates by error type (validation, connection, permission, system, payment)
👉 **For BMW apps:** See [`density-error-messages.md`](density-error-messages.md) for BMW-specific principles

- Links distinguishable from surrounding text?

**Good patterns:**

- ✅ "View pricing details"
- ✅ "Read the documentation"
- ✅ "Contact support"
- ✅ Link text that clearly describes destination

**Bad patterns:**

- ❌ "Click here" (where?)
- ❌ "More" (more what?)
- ❌ "Read more" (read more about what?)
- ❌ Icon-only links without visible text

---

### 7. Headings & Hierarchy (MANDATORY)

- [ ] **H1 text** — Page title
- Flag these anti-patterns:\*\*
- ❌ "Click here", "here", "read more", "learn more" (non-descriptive)
- ❌ Icon-only links without visible text
- ❌ Link text that doesn't make sense out of context

### 8. Empty States (if visible)

- [ ] **Empty state messaging** — No data / no results scenarios
- [ ] **Empty state actions** — CTA to add first item

**Good patterns:**

- ✅ Explains why empty: "No projects yet"
- ✅ Provides action: "Create your first project to get started"
- ✅ Offers help: "Need help getting started? [View tutorial]"

**Bad patterns:**

- ❌ Just shows blank screen (no message)
- ❌ Generic: "No data"
- ❌ No suggested action: "Nothing here" (now what?)

---

## Evaluation:

- Explains why empty? ("No projects yet" vs generic "No data")
- Provides actionable next step? ("Create your first project")
- Offers help when appropriate? (Link to tutorial or guide)

**Flag when:**

- No message (just blank screen)
- Generic message without context: "No data", "Nothing here"
- No suggested action or next step

👉 **See [`copy-patterns.md` → Empty States](copy-patterns.md#empty-states)** for patterns by type (first-use, user-cleared, search/filter, error

- Timestamps specific enough? ("Just now" vs "2:34 PM")

---

## Common Content Anti-Patterns

### 1. Placeholder as Label

**Problem:** Placeholder disappears when user starts typing, leaving users unsure of field purpose.

```html
❌ <input type="email" placeholder="Email address" />

✅ <label for="email">Email address</label>
<input type="email" id="email" placeholder="name@company.com" />
```

---

### 2. Generic Button Labels

**Problem:** User must remember context to understand action.

**Examples:**

- ❌ "Submit" (submit what?)
- ❌ "OK" (okay to what?)
- ❌ "Save" (save what? where?)

**Solutions:**

- ✅ "Save profile changes"
- ✅ "Submit application"
- ✅ "Confirm deletion"

---

### 3. Vague Error Messages

**Problem:** User doesn't know what went wrong or how to fix it.

**Examples:**

- ❌ "Error occurred"
- ❌ "Invalid input"
- ❌ "Something went wrong"

**Solutions:**

- ✅ "Unable to save. Check your internet connection and try again."
- ✅ "Password must be at least 8 characters with a number."
- ✅ "Email must include @ symbol."

---

### 4. Non-Descriptive Link Text

**Problem:** Generic link text doesn't describe destination. Users can't predict where the link will take them.

**Examples:**

- ❌ "Click here for more information"
- ❌ "Read more"
- ❌ "Learn more" (about what?)

**Solutions:**

- ✅ "View pricing details"
- ✅ "Read the onboarding guide"
- ✅ "Learn about BMW design systems"

---

### 5. Inconsistent Terminology

**Problem:** Users unsure if different words mean different actions.

**Examples:**

- ❌ "Delete" in one place, "Remove" in another
- ❌ "Sign in" vs "Log in" vs "Login"
- ❌ "Settings" vs "Preferences" vs "Options"

**Solution:** Pick ONE term and use it everywhere. Document the choice.

---

### 6. Jargon & Technical Language

**Problem:** Users unfamiliar with technical terms struggle to understand.

**Examples:**

- ❌ "Initialize SSO authentication protocol"
- ✅ "Sign in with your company account"
- ❌ "Flush cache and reinitialize"
- ✅ "Clear cache and reload"

**Test:** Would your non-technical family member understand this?

---

### 7. Missing Context

**Problem:** Message or label lacks sufficient context to be actionable.

**Examples:**

- ❌ "This step is not relevant." (why? what now?)
- ❌ "Feature unavailable." (for whom? how to get access?)
- ❌ "Processing" (how long? what's being processed?)

**Solutions:**

- ✅ "This step doesn't apply to internal users. You already have access. [View other steps]"
- ✅ "This feature is for premium users. [Upgrade] or [view free alternatives]"
- ✅ "Uploading your file... 60% complete"

---

## Integration with Nielsen Heuristics

When evaluating content, always **link to relevant Nielsen heuristics**. This shows that content quality directly impacts usability.

**Quick reference:**

- **Vague error messages** → H9 (Error recovery)
- **Generic button labels** → H6 (Recognition)
- **Inconsistent terminology** → H4 (Consistency)
- **Missing field labels** → H6 (Recognition)
- **Jargon / technical language** → H2 (Match real world)
- **No success confirmation** → H1 (Visibility of status)
- **Missing helper text** → H5 (Error prevention)

See [`content-to-heuristic-mapping.md`](content-to-heuristic-mapping.md) for complete mapping table.

---

## Density Voice & Tone Guidelines (BMW)

When auditing BMW applications, reference Density design system standards:

### Voice Characteristics

- **Professional** — Not overly casual or playful
- **Clear** — Direct, straightforward language
- **Respectful** — Acknowledges user agency
- **Confident** — Declarative, not tentative

### Tone by Context

- **Success:** Brief, confident ("Changes saved")
- **Error:** Helpful, solution-focused ("Unable to save. Check connection and try again.")
- **Warning:** Clear, actionable ("Unsaved changes will be lost. Continue?")
- **Empty state:** Encouraging, guiding ("No projects yet. Create your first project.")

### Word Choice

- **Use:** "You" (not "the user")
- **Use:** Active voice ("Save changes" not "Changes will be saved")
- **Avoid:** Exclamation marks (except true celebrations)
- **Avoid:** Emojis (except in informal community spaces)
- **Avoid:** "Please" (respectful but concise: "Enter your email" not "Please enter your email")

**For complete Density guidelines, reference:**

- `ux-writing/references/density-voice-and-tone.md`
- `ux-writing/references/density-action-labels.md`
- `ux-writing/references/density-error-messages.md`

---

## Finding Template: Content Issues

When documenting content issues, use this structure:

- [`density-voice-and-tone.md`](density-voice-and-tone.md) — Voice characteristics, perspective, related resources
- [`density-action-labels.md`](density-action-labels.md) — 50+ BMW-approved action labels (English/German)
- [`density-error-messages.md`](density-error-messages.md) — Error message principles with examples
- [`density-numerics.md`](density-numerics.md) — Date, time, number, phone, currency formatting
- [`density-text.md`](density-text.md) — Spelling, capitalization, punctuation, gendering
  **Current Copy:**
  "[exact current text]"

**Issue:**
[Specific problem — too vague, generic, inconsistent, missing context]

**Impact:**

- [How this affects users]
- [Task completion impact]
- [Support/confusion risk]

**Recommendation:**
"[improved copy]"

**Rationale:**
[Why this is better — maps to which UX writing principle and Nielsen heuristic]

**Priority:** [LOW/MEDIUM/HIGH based on impact]

````

**Example:**

```markdown
### Button label is too generic

**Current Copy:**
"Submit"

**Issue:**
Generic button label doesn't indicate what will be submitted or what happens next. Violates H6 (Recognition rather than recall).

**Impact:**
- Users must remember form context to understand action
- Increases cognitive load, especially for first-time users
- May lead to accidental submissions if context unclear

**Recommendation:**
"Save profile changes"

**Rationale:**
Descriptive label eliminates need to recall context. Users immediately recognize what action will be taken. Combines verb + object for clarity (UX writing principle: Clarity).

**Priority:** MEDIUM — Improves clarity and reduces confusion
````

---

## Summary

Good UX writing is:

- ✅ **Clear** — One meaning, no ambiguity
- ✅ **Concise** — No unnecessary words
- ✅ **Helpful** — Guides users toward success
- ✅ **Consistent** — Same terms throughout
- ✅ **Accessible** — Works for all users
- ✅ **On-brand** — Matches voice/tone guidelines

During Phase 3 of ux-reviewer:

1. **Inventory** all interface text (search, buttons, nav, forms, errors, links, headings)
2. **Evaluate** against 6 principles
3. **Link** content issues to Nielsen heuristics
4. **Document** findings with before/after recommendations
5. **Prioritize** based on impact and heuristic violation severity

Remember: **Content quality = Usability quality**. Vague copy isn't just poor writing — it's a violation of Nielsen's usability principles.

---

## Related Resources

- **[`copy-patterns.md`](copy-patterns.md)** — Ready-to-use templates for buttons, errors, forms, empty states, confirmations, and more (organized by UI component)
- **[`content-to-heuristic-mapping.md`](content-to-heuristic-mapping.md)** — Complete mapping of content issues to Nielsen heuristics
- **[`integrated-finding-templates.md`](integrated-finding-templates.md)** — Templates for writing integrated findings that combine content + usability issues
- **BMW Density references:** [`density-voice-and-tone.md`](density-voice-and-tone.md), [`density-action-labels.md`](density-action-labels.md), [`density-error-messages.md`](density-error-messages.md), [`density-numerics.md`](density-numerics.md), [`density-text.md`](density-text.md), [`density-imprint.md`](density-imprint.md)
