# Detecting and Handling Scope Creep

## What is Scope Creep in PRs?

Scope creep occurs when a PR includes changes that extend beyond the original intended purpose. This makes PRs harder to review, increases risk, and can delay merge.

## Detection Strategies

### 1. File Pattern Analysis

Changes to unrelated file types often indicate scope creep:

```
Feature: "Add user authentication"
Files changed:
  ✓ src/auth/login.ts
  ✓ src/auth/session.ts
  ⚠️ src/database/migrations/001_add_indexes.sql  # Database optimization?
  ⚠️ docs/deployment.md                            # Unrelated docs update?
  ⚠️ package.json                                   # Dependency update?
```

### 2. Commit Message Analysis

Look for commits with different focuses:

```
✓ feat: implement JWT authentication
✓ feat: add login endpoint
✓ test: add authentication tests
⚠️ refactor: improve database connection pooling  # Different concern
⚠️ fix: correct typo in README                     # Housekeeping
```

### 3. Directory Boundary Analysis

Changes spanning multiple top-level domains:

```
Ticket: "Fix payment gateway timeout"
Directories touched:
  ✓ src/payments/
  ⚠️ src/notifications/  # Why is notification code changing?
  ⚠️ src/analytics/       # Analytics changes seem unrelated
```

### 4. Ticket Description Comparison

Compare ticket requirements with actual changes:

```
Ticket PROJ-123: "Add CSV export functionality"

Expected changes:
  - CSV generation logic
  - Export button in UI
  - Tests for CSV format

Actual changes include:
  ✓ CSV generation
  ✓ Export button
  ✓ CSV tests
  ⚠️ Refactored data fetching layer  # Not mentioned in ticket
  ⚠️ Updated API error handling       # Seems like a separate improvement
```

## Handling Scope Creep

### When to Split

Split into separate PRs when:

- Changes address multiple distinct problems
- Changes could be deployed independently
- Changes require different reviewers (domain experts)
- Changes have different risk levels
- Changes have different testing requirements

### When to Keep Together

Keep in one PR when:

- Changes are tightly coupled (one depends on the other)
- Splitting would result in broken state
- Changes are very small (< 50 lines total)
- Changes are part of the same refactoring pass
- Separating would complicate deployment

### Splitting Workflow

1. **Identify split points**

   ```bash
   # List commits in current branch
   git log main..HEAD --oneline

   # Look for natural boundaries between concerns
   ```

2. **Create new branch for secondary changes**

   ```bash
   git checkout -b feature/secondary-concern main
   git cherry-pick <commit-hash1> <commit-hash2>
   git push -u origin feature/secondary-concern
   ```

3. **Remove secondary changes from original branch**

   ```bash
   git checkout feature/original-concern
   git rebase -i main
   # Mark secondary commits as 'drop' in interactive rebase
   ```

4. **Update commit messages if needed**
   ```bash
   git rebase -i main
   # Edit commit messages to clarify scope
   ```

## Communication Templates

### Asking User About Split

```
I've analyzed the changes and noticed some potential scope creep:

**Primary concern (matches ticket PROJ-123):**
- Add CSV export button
- Implement CSV generation
- Add export tests

**Additional changes (not in ticket):**
- Refactor data fetching layer (15 files)
- Update API error handling (8 files)

The additional changes seem valuable but unrelated to the CSV export feature.

Would you like me to:
A. Keep everything in one PR (I'll add explanation to description)
B. Split into two PRs: one for CSV export, one for refactoring
C. Move the additional changes to a separate branch for later

My recommendation: B (easier to review and deploy independently)
```

### Explaining Combined Scope

If user chooses to keep everything together:

```markdown
## Summary

Adds CSV export functionality and refactors data fetching layer.

**Note:** This PR combines two related improvements:

1. CSV export feature (addresses PROJ-123)
2. Data fetching refactor (enables better export performance)

The refactoring was included here because:

- CSV export requires efficient data fetching
- Changes are tightly coupled
- Separating would delay CSV export delivery

## What changed

### CSV Export (PROJ-123)

- Added export button to data table UI
- Implemented CSV generation service
- Added format validation and tests

### Data Fetching Refactor

- Refactored repository layer for better streaming
- Updated query builders for export use case
- Added pagination support for large exports
```

## Automated Detection Checklist

When analyzing a branch, check:

- [ ] Are file changes grouped by directory/domain?
- [ ] Do commit messages have consistent prefixes?
- [ ] Do changed files share common imports/dependencies?
- [ ] Is there a clear narrative in the commit history?
- [ ] Do changes align with branch name?
- [ ] Do changes match any referenced ticket/issue?
- [ ] Could any changes be deployed independently?
- [ ] Are there "while I was here" fixes?

## Examples of Scope Creep

### Example 1: Feature + Unrelated Cleanup

**Branch:** `feature/add-dark-mode`

**Changes:**

- ✓ Dark mode theme implementation
- ✓ Theme switcher component
- ⚠️ Fix typos in 20 unrelated files
- ⚠️ Update copyright year in headers

**Action:** Split typo fixes into separate "chore: fix typos" PR

### Example 2: Bug Fix + Performance Optimization

**Branch:** `fix/login-redirect-bug`

**Changes:**

- ✓ Fix redirect after login
- ⚠️ Optimize database indexes
- ⚠️ Add caching layer

**Action:** Keep bug fix, move optimizations to `perf/improve-login-performance` PR

### Example 3: Feature + Breaking Change

**Branch:** `feature/add-webhooks`

**Changes:**

- ✓ Webhook delivery system
- ✓ Webhook configuration UI
- ⚠️ Rename API endpoints (breaking change)

**Action:** Definitely split - breaking changes need separate review and migration plan
