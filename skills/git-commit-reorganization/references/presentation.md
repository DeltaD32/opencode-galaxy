---
name: Presentation
category: git-commit-reorganization
description: Present commit reorganization results to user with before/after comparison and provide restoration options
---

# Presentation Skill

## Purpose

Presents commit reorganization results to the user by:

- Showing before/after comparison
- Highlighting improvements
- Providing evidence of data integrity
- Offering approval/rejection options with clear consequences

## Presentation Format

### Summary Overview

**Present high-level comparison**:

```markdown
# Commit Reorganization Complete! 🎉

## Summary

**Before**:

- 3 commits with generic messages
- 35 files total
- Average 11.7 files per commit

**After**:

- 8 atomic commits with conventional messages
- 35 files total (all preserved)
- Average 4.4 files per commit

**Improvements**:

- ✓ Commits are more atomic (fewer files per commit)
- ✓ Messages follow conventional commit format
- ✓ Changes are logically grouped
- ✓ History is more reviewable and maintainable
```

### Before/After Commit Messages

**Show side-by-side comparison**:

```markdown
## Commit Messages: Before vs After

### Before (3 commits)

1. `WIP: authentication work` (15 files)
2. `more updates` (8 files)
3. `final changes` (12 files)

### After (8 commits)

1. `chore(config): add authentication configuration` (1 file)
2. `feat(auth): add JWT token validation` (3 files)
3. `test(auth): add JWT validation tests` (1 file)
4. `feat(user): implement user model and service` (2 files)
5. `feat(api): add user management endpoints` (1 file)
6. `test(user): add user model and API tests` (2 files)
7. `docs(api): document authentication API endpoints` (1 file)
8. `docs: update README with authentication setup` (2 files)
```

### Detailed Commit Breakdown

**Show each new commit with files**:

```markdown
## New Commit Structure

### 1. chore(config): add authentication configuration

**Files** (1):

- config/auth.config.js

**Rationale**: Configuration needed by auth logic

---

### 2. feat(auth): add JWT token validation

**Files** (3):

- src/auth/jwt.js
- src/auth/validator.js
- src/auth/middleware.js

**Rationale**: Core authentication functionality

---

### 3. test(auth): add JWT validation tests

**Files** (1):

- tests/auth/jwt.test.js

**Rationale**: Tests for JWT implementation

---

[... continue for all commits ...]
```

### Verification Results

**Show evidence of data integrity**:

```markdown
## Verification Results

### Data Integrity ✓

- Git diff verification: **PASSED** (no differences detected)
- File count verification: **PASSED** (35 files in both)
- All original changes preserved exactly

### Build & Tests

- Build: **PASSED** ✓
- Tests: **PASSED** (127 tests, 0 failures) ✓
- Linting: **PASSED** (3 warnings, non-critical) ⚠

### Overall: ✓ SUCCESS

All changes preserved correctly. Safe to proceed.
```

### Restoration Instructions

**Always provide escape hatch**:

```markdown
## Restoration Instructions

If you want to revert to the original commits:

\`\`\`bash
git reset --hard backup/feature-user-authentication-20260115-143000
\`\`\`

This will restore:

- Original 3 commits
- Original commit messages
- Exact same code state

The backup branch will remain until you explicitly delete it.
```

## User Decision Options

### Present Three Options

```markdown
## What would you like to do?

### (A) Approve and Keep New Commits ✅

- Delete the backup branch
- Keep the new atomic commits
- **Recommended** if you're satisfied with the results

### (B) Reject and Restore from Backup ↩️

- Restore original commits from backup
- Delete new atomic commits
- Keep backup branch for reference
- **Use this** if you're not satisfied with the reorganization

### (C) Keep Both for Now 🤔

- Keep both backup and new commits
- Decide later which to use
- **Use this** if you need more time to review

**What would you like to do? (A/B/C)**
```

### Handle User Choice

**Option A: Approve**

```javascript
async function handleApproval() {
  console.log("You chose: (A) Approve and keep new commits");

  // Confirm deletion of backup
  console.log("\nThis will:");
  console.log("- Delete backup branch (cannot be undone)");
  console.log("- Keep new atomic commits");
  console.log("- Mark reorganization as complete");
  console.log("\nAre you sure? (Y/N)");

  const confirmed = await getUserConfirmation();

  if (confirmed) {
    // Delete backup branch
    const backupBranch = state.flowSpecificData.backupBranch;
    execSync(`git branch -D ${backupBranch}`);
    console.log(`✓ Deleted backup branch: ${backupBranch}`);

    // Mark state as completed
    updateStateAsCompleted();

    // Ask about state directory
    console.log("\nKeep workflow state directory for reference? (Y/N)");
    const keepState = await getUserConfirmation();

    if (!keepState) {
      execSync("rm -rf .ttt/memory/ttt-nice-git-commits/");
      console.log("✓ Removed workflow state directory");
    }

    console.log("\n✅ Commit reorganization approved and completed!");
  } else {
    console.log("Approval cancelled. Backup branch preserved.");
  }
}
```

**Option B: Reject and Restore**

```javascript
async function handleRejection() {
  console.log("You chose: (B) Reject and restore from backup");

  // Confirm restoration
  console.log("\nThis will:");
  console.log("- Restore original commits from backup");
  console.log("- Delete new atomic commits (cannot be undone)");
  console.log("- Delete workflow state");
  console.log("\nAre you sure? (Y/N)");

  const confirmed = await getUserConfirmation();

  if (confirmed) {
    // Restore from backup
    const backupBranch = state.flowSpecificData.backupBranch;
    execSync(`git reset --hard ${backupBranch}`);
    console.log(`✓ Restored from backup: ${backupBranch}`);

    // Verify restoration
    console.log("\nVerifying restoration...");
    execSync("git status");
    execSync("git log --oneline -5");

    // Clean up state directory
    execSync("rm -rf .ttt/memory/ttt-nice-git-commits/");
    console.log("✓ Removed workflow state directory");

    console.log(
      "\n✅ Restored to original commits. Backup branch preserved for reference.",
    );
    console.log(
      `\nYou can delete the backup branch when ready: git branch -D ${backupBranch}`,
    );
  } else {
    console.log("Restoration cancelled. New commits remain.");
  }
}
```

**Option C: Keep Both**

```javascript
async function handleKeepBoth() {
  console.log("You chose: (C) Keep both for now");

  console.log("\nBoth versions are preserved:");
  console.log(
    `- New commits: ${state.flowSpecificData.currentBranch} (current)`,
  );
  console.log(`- Original commits: ${state.flowSpecificData.backupBranch}`);

  console.log("\nYou can:");
  console.log("- Continue working with new commits");
  console.log(
    "- Switch to backup: git checkout " + state.flowSpecificData.backupBranch,
  );
  console.log(
    "- Delete backup when ready: git branch -D " +
      state.flowSpecificData.backupBranch,
  );
  console.log("- Re-run this flow to make adjustments");

  // Mark state as completed-pending-approval
  updateStateAsPendingApproval();

  console.log("\n✅ Both versions preserved. Decide when ready.");
}
```

## Comparison Artifact Generation

### Generate Before/After Document

```javascript
function generateComparisonDocument(state) {
  const original = state.flowSpecificData.originalCommits;
  const newCommits = state.flowSpecificData.newCommits;

  const document = `
# Commit Reorganization: Before/After Comparison

Generated: ${new Date().toISOString()}
Branch: ${state.flowSpecificData.currentBranch}

## Original Commits (${original.length})

${original
  .map(
    (c, i) => `
### ${i + 1}. ${c.message}
**Hash**: ${c.hash}
**Files**: ${c.filesChanged}
**Timestamp**: ${c.timestamp}
`,
  )
  .join("\n")}

## New Atomic Commits (${newCommits.length})

${newCommits
  .map(
    (c, i) => `
### ${i + 1}. ${c.message}
**Hash**: ${c.hash}
**Files**: ${c.filesChanged}
**Timestamp**: ${c.timestamp}
`,
  )
  .join("\n")}

## Statistics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Commit count | ${original.length} | ${newCommits.length} | ${
    newCommits.length > original.length ? "+" : ""
  }${newCommits.length - original.length} |
| Total files | ${original.reduce(
    (sum, c) => sum + c.filesChanged,
    0,
  )} | ${newCommits.reduce(
    (sum, c) => sum + c.filesChanged,
    0,
  )} | 0 (preserved) |
| Avg files/commit | ${(
    original.reduce((sum, c) => sum + c.filesChanged, 0) / original.length
  ).toFixed(1)} | ${(
    newCommits.reduce((sum, c) => sum + c.filesChanged, 0) / newCommits.length
  ).toFixed(1)} | ${(
    newCommits.reduce((sum, c) => sum + c.filesChanged, 0) / newCommits.length -
    original.reduce((sum, c) => sum + c.filesChanged, 0) / original.length
  ).toFixed(1)} |

## Conventional Commit Compliance

**Before**:
${original.filter((c) => isConventionalCommit(c.message)).length}/${
    original.length
  } commits follow conventional format

**After**:
${newCommits.filter((c) => isConventionalCommit(c.message)).length}/${
    newCommits.length
  } commits follow conventional format

## Restoration Command

\`\`\`bash
git reset --hard ${state.flowSpecificData.backupBranch}
\`\`\`
`;

  // Save to artifacts
  writeFile(
    ".ttt/memory/ttt-nice-git-commits/artifacts/commit-comparison.md",
    document,
  );

  return document;
}
```

## Presentation Best Practices

### Lead with Success

```markdown
# ✅ Commit Reorganization Successful!

All changes preserved. Ready for review.
```

Not:

```markdown
# Commit Reorganization Complete

Results below.
```

### Show Clear Evidence

**Include verification proof**:

- ✓ Git diff: No differences
- ✓ File count: Match
- ✓ Build: Passed
- ✓ Tests: Passed

**Not just**: "Verification passed"

### Provide Escape Hatch Prominently

**Always show restoration command early**:

```markdown
## Quick Restore

Not happy with results? Restore immediately:

\`\`\`bash
git reset --hard backup/branch-name-timestamp
\`\`\`
```

**Not buried at bottom of long document**

### Use Visual Comparisons

**Before/After side-by-side** is clearer than separate sections:

```markdown
| Aspect              | Before | After |
| ------------------- | ------ | ----- |
| Commits             | 3      | 8     |
| Avg files/commit    | 11.7   | 4.4   |
| Conventional format | 0/3    | 8/8   |
```

### Make Options Crystal Clear

```markdown
## What would you like to do?

### (A) ✅ Approve

Keep new commits, delete backup

### (B) ↩️ Reject

Restore from backup, delete new

### (C) 🤔 Decide Later

Keep both for now

**Choose: A, B, or C**
```

**Not**: "What do you want to do with these commits?"

## Error Presentation

### If Verification Failed

```markdown
## ⚠️ Verification Failed

**Status**: Changes differ from backup (NOT SAFE)

**Issue**: Git diff detected differences between backup and new commits.
This means some changes were lost or modified during reorganization.

**Recommendation**: Restore from backup immediately.

**What happened**:
${diffSummary}

**Options**:
(A) Restore from backup NOW (recommended)
(B) Review diff first, then decide

**Choose: A or B**
```

### If Build/Tests Failed

```markdown
## ⚠️ Build/Tests Failed (Non-Critical)

**Status**: All changes preserved, but build/tests failing

**Git Verification**: ✓ PASSED (no changes lost)
**Build**: ✗ FAILED
**Tests**: ✗ FAILED

**Possible causes**:

1. Commits in wrong order (dependencies not respected)
2. Build/tests were already failing on backup branch
3. Tests grouped incorrectly

**Options**:
(A) Restore and adjust commit plan
(B) Keep commits and fix build manually
(C) Review commit order

**Choose: A, B, or C**
```

## Post-Approval Actions

### Mark Complete in State

```javascript
function updateStateAsCompleted() {
  const state = loadState(".ttt/memory/ttt-nice-git-commits/state.json");

  // Mark all steps as completed
  state.steps.forEach((step) => {
    if (step.status !== "completed") {
      step.status = "completed";
      step.completedAt = new Date().toISOString();
    }
  });

  // Mark flow as completed
  state.flowStatus = "completed";
  state.completedAt = new Date().toISOString();
  state.userApproved = true;

  saveState(".ttt/memory/ttt-nice-git-commits/state.json", state);
}
```

### Cleanup Recommendations

```javascript
function provideCleanupGuidance() {
  console.log(`
Next steps:

1. Review the new commit history:
   git log --oneline

2. If working on a feature branch, you may need to force push:
   git push --force-with-lease origin ${state.flowSpecificData.currentBranch}

   ⚠️ WARNING: Only force push if:
   - This is a personal/feature branch
   - No one else has pulled your commits
   - You've communicated with your team

3. Create a pull request with clean commit history

4. The workflow state is saved in:
   .ttt/memory/ttt-nice-git-commits/

   You can delete this directory when no longer needed.
`);
}
```

## References

- **Main Skill**: [SKILL.md](SKILL.md)
- **State Management**: [state-management.md](state-management.md)
- **Verification**: [verification.md](verification.md)
- **Agent Prompt**: [../../agents/nice-git-commits.agent.md](../../agents/nice-git-commits.agent.md)
