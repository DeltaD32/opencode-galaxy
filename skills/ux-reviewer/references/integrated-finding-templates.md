# Integrated Finding Templates

## Purpose

Provides **ready-to-use templates** for writing integrated findings that combine Nielsen heuristics and UX writing perspectives. These templates ensure findings are actionable, comprehensive, and demonstrate the usability impact of content issues.

---

## Template Structure

Every integrated finding should include:

1. **Issue Title** — Clear, specific description (not generic)
2. **Heuristic(s)** — Which Nielsen principle(s) violated
3. **Content Problem** — What's wrong with the interface text
4. **Usability Impact** — How this affects user goals (not just "unclear")
5. **Severity** — Based on both heuristic and content impact
6. **Current State** — Screenshot or code showing the problem
7. **Recommendation** — Specific fix with before/after examples
8. **Rationale** — Why this improves both usability and content

---

## Template 1: Vague Error Message

```markdown
### [Error type] message lacks actionable guidance

**Heuristic:** H9 - Help users recognize, diagnose, and recover from errors
**Severity:** HIGH

**Content Problem:**
Error message "[current text]" is vague and doesn't explain what went wrong or how to fix it.

**Current State:**
[Screenshot of error]
```

❌ **Current:** "[vague error text]"

```
**Usability Impact:**
- Users can't diagnose the root cause of the error
- No clear recovery path provided
- Increases support ticket volume and user frustration
- May cause users to abandon task entirely

**Recommendation:**
```

✅ **Improved:** "[Specific error with cause and fix]"

```
**Example:**
```

❌ Before: "Error occurred"
✅ After: "Unable to save changes. Check your internet connection and try again. [Retry]"

```
**Rationale:**
Improved error message combines clear problem explanation (content) with actionable recovery steps (usability). Users understand what went wrong and know exactly what to do next.

**Priority:** HIGH — Quick win, high impact on user confidence
```

---

## Template 2: Generic Button Label

````markdown
### "[Button text]" button lacks descriptive context

**Heuristic:** H6 - Recognition rather than recall
**Severity:** MEDIUM

**Content Problem:**
Button labeled "[generic text]" requires users to remember what action will be performed, rather than recognizing it from the label itself.

**Current State:**
[Screenshot of button]

```html
<button>[generic text]</button>
```
````

**Usability Impact:**

- Users must reconstruct context to understand button action
- Increases cognitive load, especially for first-time users
- May lead to accidental actions if user misremembers context
- Reduces clarity and efficiency

**Recommendation:**

```html
✅ <button>[specific descriptive text]</button>
```

**Examples:**

| Context          | ❌ Generic    | ✅ Descriptive               |
| ---------------- | ------------- | ---------------------------- |
| Profile editing  | "Submit"      | "Save profile changes"       |
| Account deletion | "OK"          | "Confirm deletion"           |
| Form submission  | "Go"          | "Continue to payment"        |
| Onboarding       | "Create step" | "Create new onboarding step" |

**Rationale:**
Descriptive button labels eliminate the need to recall context. Users immediately recognize what action will be taken, reducing errors and improving efficiency.

**Priority:** MEDIUM — Improves clarity and reduces confusion

````

---

## Template 3: Inconsistent Terminology

```markdown
### Inconsistent terminology for [action/concept] across interface

**Heuristic:** H4 - Consistency and standards
**Severity:** MEDIUM

**Content Problem:**
The same action/concept is described using different terms in different locations:
- Location A: "[term 1]"
- Location B: "[term 2]"
- Location C: "[term 3]"

**Current State:**
[Screenshots showing different terms]

**Usability Impact:**
- Users unsure if different terms mean different actions
- Creates doubt about system behavior
- Increases learning curve as users must memorize multiple terms
- May cause users to search for a feature they've already seen under different name

**Recommendation:**
Standardize on a single term throughout the entire interface.

**Recommended term:** "[chosen term]"

**Rationale for choice:**
- Most commonly used in the domain
- Matches user mental model
- Clear and unambiguous
- Density design system standard (if applicable)

**Changes Required:**
- [ ] Screen X: Change "[old term]" to "[new term]"
- [ ] Screen Y: Change "[old term]" to "[new term]"
- [ ] Help docs: Update terminology
- [ ] Error messages: Use consistent term

**Priority:** MEDIUM — Affects learnability and user confidence
````

---

## Template 4: Truncated Text Hiding Critical Info

````markdown
### [Element type] displays truncated text "[truncated...]"

**Heuristic:** H4 - Consistency and standards, H6 - Recognition rather than recall
**Severity:** HIGH

**Content Problem:**
[Element] shows "[truncated text]" instead of displaying the full selection "[full text]", preventing users from seeing critical information.

**Current State:**
[Screenshot showing truncation]

```html
<[element]>[truncated text]<[/element]>
```
````

**Usability Impact:**

- Users can't see their current selection without opening [element]
- Must repeatedly interact with [element] to confirm choice
- Violates principle of making options visible
- Increases task completion time and user frustration
- May cause users to miss that they have wrong selection active

**Recommendation:**

**Option 1: Expand to show full text**

```html
<[element]>[full text]<[/element]>
```

**Option 2: Intelligent truncation** (if space constrained)

```html
<[element]>[truncated at word boundary...]<[/element]>
```

- Truncate at word boundary, not mid-word
- Add tooltip showing full text on hover

**Option 3: Abbreviation pattern**

```html
<[element]>[abbreviated version]<[/element]>
```

- Use accepted abbreviation: e.g., "BMW Group" instead of "BMW Group Internal"

**Rationale:**
Visibility of current selection is fundamental to usable form controls. Truncation that hides meaningful information degrades both recognition and consistency.

**Priority:** HIGH — Critical visibility issue affecting user confidence

````

---

## Template 5: Missing Field Label

```markdown
### [Field type] missing persistent label

**Heuristic:** H6 - Recognition rather than recall
**Severity:** MEDIUM to HIGH (depending on field importance)

**Content Problem:**
[Field] has placeholder text "[placeholder]" but no visible label. Placeholder disappears when user starts typing, leaving users unsure of field purpose.

**Current State:**
```html
<input type="[type]" placeholder="[placeholder]" />
````

**Usability Impact:**

- Placeholder text not persistently visible — users forget field purpose
- Users with cognitive disabilities particularly affected
- Violates recognition over recall principle

**Recommendation:**

**Best practice: Visible label + placeholder**

```html
<label for="[id]">[Label text]</label>
<input type="[type]" id="[id]" placeholder="[optional example]" />
```

**If space constrained: Floating label pattern**

```html
<div class="floating-label">
  <input type="[type]" id="[id]" placeholder=" " />
  <label for="[id]">[Label text]</label>
</div>
```

**Rationale:**
Persistent labels are essential for recognition. Placeholders alone are insufficient and violate established usability principles.

**Priority:** HIGH (for required fields), MEDIUM (for optional fields)

````

---

## Template 6: Non-Standard Instructions

```markdown
### [Instruction location] uses non-standard phrasing that increases cognitive load

**Heuristic:** H2 - Match between system and the real world
**Severity:** MEDIUM

**Content Problem:**
Instruction "[non-standard text]" uses unusual phrasing that doesn't match user expectations or common patterns.

**Current State:**
[Screenshot]
````

"[non-standard text]"

```
**Usability Impact:**
- Users must parse unusual instruction format
- Increases cognitive load and task completion time
- May be interpreted incorrectly, leading to user errors
- Creates unfamiliarity with interface, reducing confidence

**Recommendation:**
```

✅ "[standard phrasing]"

```
**Why this is better:**
- Uses familiar language from user's domain
- Matches patterns from other applications
- Immediately clear without interpretation
- Reduces cognitive effort

**Examples:**

| Context | ❌ Non-standard | ✅ Standard |
|---------|----------------|------------|
| Global search | "Type ''/'' to search" | "Search Developer Home" |
| Field format | "Use pattern DD.MM.YYYY" | "Format: DD/MM/YYYY" or "Example: 25/12/2026" |
| Required field | "This is mandatory" | "Required" |

**Priority:** MEDIUM — Language clarity improvement
```

---

## Template 7: Missing Page Introduction

````markdown
### Page lacks introductory context below heading

**Heuristic:** H2 - Match between system and the real world
**Severity:** LOW

**Content Problem:**
Page title "[H1 text]" has no supporting description or introduction. First-time users lack orientation about page purpose and available actions.

**Current State:**

```html
<h1>[H1 text]</h1>
<!-- Immediately followed by content, no introduction -->
```
````

**Usability Impact:**

- First-time users don't understand page purpose without exploration
- Term "[H1 text]" may not be immediately clear to all users
- Missing opportunity to set expectations and guide users
- Reduces discoverability of available features

**Recommendation:**
Add 1-2 sentence introduction below the H1 that:

1. Explains what the page offers
2. Guides users toward primary actions
3. Uses plain language, not terminology

**Example:**

```html
<h1>[H1 text]</h1>
<p class="page-intro">
  [1-2 sentence description explaining page purpose and what users can do here]
</p>
```

**Sample introductions:**

| Page Type          | Introduction                                                                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Onboarding Journey | "Complete these self-guided steps to set up your developer accounts and get started with BMW tools and services."                                       |
| Dev Resources      | "Browse BMW's curated library of approved frameworks, tools, and services for application development. Filter by category, status, or technology."      |
| Dashboard          | "Your personalized overview of active projects, recent updates, and quick actions. Check status, view notifications, and access frequently-used tools." |

**Priority:** LOW — UX enhancement for first-time users, quick content addition

````

---

## Template 8: Missing Autocomplete/Suggestions

```markdown
### Search/filter input lacks autocomplete suggestions

**Heuristic:** H7 - Flexibility and efficiency of use, H5 - Error prevention
**Severity:** LOW

**Content Problem:**
[Input field] with placeholder "[placeholder]" provides no autocomplete or type-ahead suggestions, forcing users to know exact names.

**Current State:**
[Screenshot]
```html
<input type="text" placeholder="[placeholder]" />
````

**Interactive Testing:**
Typed "[test input]" → No suggestions appeared after 400ms wait

**Usability Impact:**

- Users must know exact names to find items
- Typos lead to "no results" with no helpful corrections
- Can't discover available options through search exploration
- Reduces efficiency compared to autocomplete pattern
- Particularly problematic for large datasets

**Recommendation:**
Implement autocomplete that:

1. Shows top 5-10 matching suggestions as user types
2. Filters suggestions based on input (debounced ~300ms)
3. Highlights matching portions in bold
4. Groups suggestions by category when applicable

**Example Behavior:**

| User Types | Suggestions Shown                                     |
| ---------- | ----------------------------------------------------- |
| "reg"      | **Reg**istration, **Reg**ister YubiKey                |
| "auth"     | **Auth**entication, Strong **Auth**, Password         |
| "kub"      | **Kub**ernetes, **Kub**ernetes Guide, **Kub**e Config |

**Implementation Pattern:**

```html
<input type="text" placeholder="[placeholder]" id="search-input" />
<ul id="suggestions-listbox">
  <!-- Suggestions populated dynamically -->
</ul>
```

**Priority:** LOW — Efficiency enhancement, improves discoverability
**Effort:** MEDIUM to HIGH (requires frontend + API changes if server-side filtering needed)

````

---

## Template 9: Info Message Lacks Guidance

```markdown
### Info message provides status but no next actions

**Heuristic:** H9 - Help users recognize, diagnose, and recover from errors
**Severity:** MEDIUM

**Content Problem:**
Message "[current text]" indicates a state but doesn't explain why or guide users toward next steps.

**Current State:**
[Screenshot]
````

ⓘ [current message text]

```
**Usability Impact:**
- Users understand the state but don't know what caused it
- No clear indication of available actions
- Creates dead-end experience with no path forward
- May lead users to assume feature is broken or unavailable
- Increases support ticket volume ("Why is this not working?")

**Recommendation:**
Rewrite to include:
1. **What** — Current state (keep existing info)
2. **Why** — Brief explanation of the reason
3. **What next** — Suggested action or alternative path

**Improved message structure:**
```

ⓘ **[State].** [Reason why]. [Suggested action] or [alternative path].

```
**Example:**

| Context | ❌ Current | ✅ Improved |
|---------|-----------|------------|
| Location filter | "This step is not relevant for your selected location." | "**This step doesn't apply to BMW Group Internal users.** You've already been granted the necessary access. [Browse other steps] or [view steps for your location]." |
| Feature unavailable | "Feature not available." | "**This feature is only available to premium users.** [Upgrade to premium] or [explore free alternatives]." |
| Permission issue | "You don't have access." | "**You need editor permissions to modify this content.** Contact your team admin to request access. [View admins]" |

**Priority:** MEDIUM — Improves guidance and reduces user confusion
```

---

## How to Use These Templates

### 1. Choose the Right Template

Match your finding to the closest template based on:

- The heuristic violated
- The type of content issue
- The severity level

### 2. Fill in the Brackets

Replace all [bracketed text] with specifics from your audit:

- Actual copy from the interface
- Screenshots or code examples
- Your recommended improvements

### 3. Adjust Severity

Fine-tune severity based on:

- How critical the task/feature is
- How many users are affected
- Whether it blocks task completion or just slows it down

### 4. Customize Examples

Provide real before/after examples specific to the application you're auditing

### 5. Integrate Multiple Templates

Some findings may combine multiple issues — merge templates as needed

---

## Summary

These templates ensure **consistent, actionable, comprehensive** findings that:
✅ Link content issues to Nielsen heuristics
✅ Explain usability impact, not just "copy is unclear"
✅ Provide specific recommendations with examples
✅ Include rationale showing why the fix improves UX
✅ Set appropriate severity and priority

Use these templates to maintain high quality across all your integrated UX reviews.
