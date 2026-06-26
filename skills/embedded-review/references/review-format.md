# Review Output Format

Specification for formatting embedded code review output. Ensures consistency
across reviews and compatibility with tooling.

## Markdown Review Format

Use this structure for the main review output:

```markdown
# Code Review for ${feature_description}

## Overview

Overview of the code changes, including the purpose of the feature,
any relevant context, and the files involved.

# Suggestions

## ${emoji_type} ${Summary — include enough context to understand the suggestion}

- **Priority**: ${priority_emoji}
- **File**: ${relative/path/to/file}
- **Details**: ...
- **Example** (if applicable): ...
- **Suggested Change** (if applicable): (code snippet...)

## (other suggestions...)

...

# Summary

Overall assessment, key risks, and verdict.
```

## Type Emojis

Prefix each suggestion with a type emoji:

| Emoji |        Code         | Meaning                                                 |
| :---: | :-----------------: | ------------------------------------------------------- |
|  🔧   |     `:wrench:`      | Change request — needs to be addressed                  |
|  ❓   |    `:question:`     | Question — requires a response from the author          |
|  ⛏   |      `:pick:`       | Nitpick — does not require changes, often stylistic     |
|  ♻️   |     `:recycle:`     | Refactor suggestion — actionable, not a nitpick         |
|  💭   | `:thought_balloon:` | Concern or alternative approach — thinking out loud     |
|  👍   |       `:+1:`        | Positive feedback — something well done                 |
|  📝   |      `:memo:`       | Explanatory note or fun fact — no action required       |
|  🌱   |    `:seedling:`     | Observation for future — not blocking, but worth noting |

## Priority Emojis

Each suggestion gets a priority level:

| Emoji |  Level   | Meaning                                                 |
| :---: | :------: | ------------------------------------------------------- |
|  🔥   | Critical | Must fix before merge — bugs, security, safety          |
|  ⚠️   |   High   | Should fix — significant quality or correctness concern |
|  🟡   |  Medium  | Worth addressing — improves quality or maintainability  |
|  🟢   |   Low    | Nice to have — minor improvement, can be deferred       |

## File-Writing Protocol

When a `Review Output File:` path is provided, write incrementally to avoid
HTTP/2 GOAWAY timeouts on large reviews.

### Step 1: Initialize with header

```bash
cat > /path/to/review-result.md << 'EOF'
# Code Review for ...
## Overview
...
EOF
```

### Step 2: Append each suggestion individually

One `cat >>` per suggestion or logical group (~40 lines max):

```bash
cat >> /path/to/review-result.md << 'EOF'
## 🔧 Suggestion N — ...
* **Priority**: ⚠️
* **File**: src/module/file.cpp
* **Details**: ...
EOF
```

### Step 3: Append summary last

```bash
cat >> /path/to/review-result.md << 'EOF'
# Summary
...
EOF
```

### Step 4: Confirm

Print exactly:

```
Review written to: /abs/path/to/review-result.md
```

Do **not** repeat the review content in the chat response.

## JSON Inline Comments Format

When a `Review Comments File:` path is provided, generate a JSON file for
posting inline PR comments (compatible with `pr-review`'s `add_pr_comment.py`).

### Schema

````json
{
  "body": "Brief overall review summary (not pinned to any line)",
  "comments": [
    {
      "path": "relative/path/to/file.cpp",
      "line": 42,
      "body": "🔧 **Summary** (⚠️ High)\n\nExplanation...\n\n```suggestion\noptional code fix\n```"
    }
  ]
}
````

### Rules

1. **`body`** (top-level): Brief summary — general observations, checklist
   verdict, risks, overall impression. Not the full review.
2. **`comments`** array: Only line-specific suggestions.
3. **`line`** value: Must be the line number on the **new (right) side** of
   the diff. Verify via `git --no-pager diff` — use `+` side line numbers
   from hunk headers (`@@ -old,count +new,count @@`).
4. Each comment **`body`** must be self-contained with emoji, priority, and
   enough context to be understood inline on the PR diff.
5. Code suggestions use GitHub's suggestion syntax:
   ````
   ```suggestion
   corrected code here
   ```
   ````
6. Write JSON **after** the markdown review is complete.
7. Print: `Review comments written to: /abs/path/to/review-comments.json`
