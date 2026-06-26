---
name: Verification
category: git-commit-reorganization
description: Comprehensive integrity verification to ensure no changes were lost or modified during commit reorganization
---

# Verification Skill

## Purpose

Ensures data integrity after commit reorganization by:

- Verifying all original changes are preserved
- Confirming no unintended modifications occurred
- Testing build and test suite functionality
- Providing evidence for user confidence

## Verification Process

### Step 1: Git Diff Verification (MANDATORY)

**Primary integrity check**:

```bash
# Compare backup branch with current HEAD
# Output MUST be empty if all changes preserved exactly
git diff backup/<branch-name> HEAD
```

**Expected result**: **EMPTY OUTPUT**

If output is empty:

- ✅ All changes preserved exactly
- ✅ No modifications introduced
- ✅ Safe to proceed

If output shows differences:

- ❌ Changes lost or modified
- ❌ STOP immediately
- ❌ Restore from backup

### Step 2: File Count Verification

**Verify all files accounted for**:

```bash
# Files changed in original commits
git diff --name-only backup/<branch> main | wc -l

# Files changed in new commits
git diff --name-only HEAD main | wc -l

# These numbers MUST match
```

**Cross-check**:

```bash
# List files in both
BACKUP_FILES=$(git diff --name-only backup/<branch> main | sort)
NEW_FILES=$(git diff --name-only HEAD main | sort)

# Compare lists
if [ "$BACKUP_FILES" = "$NEW_FILES" ]; then
  echo "✓ All files accounted for"
else
  echo "✗ File mismatch detected"
  diff <(echo "$BACKUP_FILES") <(echo "$NEW_FILES")
fi
```

### Step 3: Content Hash Verification

**Verify identical content**:

```bash
# Generate tree hash for backup
BACKUP_TREE=$(git rev-parse backup/<branch>^{tree})

# Generate tree hash for current HEAD
HEAD_TREE=$(git rev-parse HEAD^{tree})

# Compare tree hashes
if [ "$BACKUP_TREE" = "$HEAD_TREE" ]; then
  echo "✓ Identical content (tree hashes match)"
else
  echo "⚠ Different tree hashes (expected - commit structure changed)"
  echo "  This is normal. Run git diff to verify changes are identical."
fi
```

**Note**: Tree hashes will differ because commit structure changed. This is expected. The critical check is `git diff` output being empty.

### Step 4: Build Verification (If Applicable)

**Test that code still builds**:

```javascript
async function verifyBuild() {
  try {
    // Read build command from project config
    const projectTools = readFile(".ttt/config/project-tools.md");
    const buildCommand = extractBuildCommand(projectTools);

    if (!buildCommand) {
      console.log(
        "ℹ No build command configured, skipping build verification",
      );
      return { skipped: true };
    }

    console.log(`Running build: ${buildCommand}`);
    execSync(buildCommand, { stdio: "inherit", timeout: 300000 }); // 5 min timeout

    console.log("✓ Build successful");
    return { success: true };
  } catch (error) {
    console.error("✗ Build failed");
    console.error(error.message);
    return { success: false, error: error.message };
  }
}
```

**Build failure handling**:

- Review commit order (dependencies may be wrong)
- Check if build was working on backup branch
- Consider if build break is acceptable (document why)

### Step 5: Test Verification (If Applicable)

**Test that tests still pass**:

```javascript
async function verifyTests() {
  try {
    // Read test command from project config
    const projectTools = readFile(".ttt/config/project-tools.md");
    const testCommand = extractTestCommand(projectTools);

    if (!testCommand) {
      console.log("ℹ No test command configured, skipping test verification");
      return { skipped: true };
    }

    console.log(`Running tests: ${testCommand}`);
    execSync(testCommand, { stdio: "inherit", timeout: 600000 }); // 10 min timeout

    console.log("✓ All tests passed");
    return { success: true };
  } catch (error) {
    console.error("✗ Tests failed");
    console.error(error.message);
    return { success: false, error: error.message };
  }
}
```

**Test failure handling**:

- Check if tests were passing on backup branch
- Review if test files were grouped correctly
- Consider if tests need reordering

### Step 6: Lint/Quality Verification (Optional)

**Check code quality maintained**:

```javascript
async function verifyQuality() {
  try {
    // Read lint command from project config
    const projectTools = readFile(".ttt/config/project-tools.md");
    const lintCommand = extractLintCommand(projectTools);

    if (!lintCommand) {
      console.log(
        "ℹ No lint command configured, skipping quality verification",
      );
      return { skipped: true };
    }

    console.log(`Running linter: ${lintCommand}`);
    execSync(lintCommand, { stdio: "inherit", timeout: 300000 });

    console.log("✓ Linting passed");
    return { success: true };
  } catch (error) {
    console.warn("⚠ Linting failed (non-critical)");
    console.warn(error.message);
    return { success: false, error: error.message, critical: false };
  }
}
```

## Verification Failure Handling

### Critical Failure: Git Diff Shows Differences

**Immediate action required**:

```bash
# Save diff output for analysis
git diff backup/<branch> HEAD > .ttt/memory/ttt-nice-git-commits/artifacts/verification-diff.txt

# Alert user
echo "CRITICAL: Verification failed - changes differ from backup"
echo "Diff saved to: .ttt/memory/ttt-nice-git-commits/artifacts/verification-diff.txt"

# Offer immediate restoration
echo "Options:"
echo "(A) Restore from backup immediately"
echo "(B) Review diff first, then decide"
```

**If user chooses restore**:

```bash
# Immediate rollback
git reset --hard backup/<branch-name>

# Verify restoration
git status
git log --oneline -5

echo "Restored to backup branch. Commit reorganization aborted."
```

**If user chooses review**:

```markdown
Show user the diff output with analysis:

**Verification Failed**

The following differences were found between the backup and new commits:

[Show diff output]

**Analysis**:

- X files have different content
- Y files are missing
- Z files were unexpectedly added

**Recommendation**: Restore from backup and investigate the issue.

Would you like to:
(A) Restore from backup
(B) Attempt manual fix
(C) Keep new commits anyway (not recommended)
```

### Non-Critical Failure: Build or Tests Fail

**Less urgent but needs attention**:

```markdown
**Build/Test Verification Failed**

The commit reorganization completed successfully (no changes lost),
but the build/tests are now failing.

**Possible causes**:

1. Commits are in wrong order (dependencies not respected)
2. Build/tests were already failing on backup branch
3. Test files were grouped incorrectly

**Options**:
(A) Restore from backup and adjust commit plan
(B) Continue with current commits and fix build/tests manually
(C) Review commit order and recreate commits

What would you like to do?
```

## Verification Report Generation

### Create Comprehensive Report

```javascript
function generateVerificationReport(results) {
  const report = {
    timestamp: new Date().toISOString(),
    gitDiff: results.gitDiff,
    fileCount: results.fileCount,
    build: results.build,
    tests: results.tests,
    quality: results.quality,
    overallSuccess: results.gitDiff.success && results.fileCount.success,
  };

  // Write to artifacts
  const reportPath =
    ".ttt/memory/ttt-nice-git-commits/artifacts/verification-results.txt";
  writeFile(reportPath, formatReport(report));

  return report;
}

function formatReport(report) {
  return `
# Verification Report
Generated: ${report.timestamp}

## Critical Checks (MUST PASS)

### Git Diff Verification
Status: ${report.gitDiff.success ? "✓ PASSED" : "✗ FAILED"}
Output: ${report.gitDiff.output || "(empty - expected)"}

### File Count Verification
Status: ${report.fileCount.success ? "✓ PASSED" : "✗ FAILED"}
Backup files: ${report.fileCount.backupCount}
New files: ${report.fileCount.newCount}
Match: ${report.fileCount.match ? "Yes" : "No"}

## Non-Critical Checks

### Build Verification
Status: ${
    report.build.skipped
      ? "ℹ SKIPPED"
      : report.build.success
        ? "✓ PASSED"
        : "✗ FAILED"
  }
${report.build.error ? `Error: ${report.build.error}` : ""}

### Test Verification
Status: ${
    report.tests.skipped
      ? "ℹ SKIPPED"
      : report.tests.success
        ? "✓ PASSED"
        : "✗ FAILED"
  }
${report.tests.error ? `Error: ${report.tests.error}` : ""}

### Quality Verification
Status: ${
    report.quality.skipped
      ? "ℹ SKIPPED"
      : report.quality.success
        ? "✓ PASSED"
        : "⚠ FAILED (non-critical)"
  }
${report.quality.error ? `Error: ${report.quality.error}` : ""}

## Overall Result
${
  report.overallSuccess
    ? "✓ VERIFICATION SUCCESSFUL - All changes preserved correctly"
    : "✗ VERIFICATION FAILED - Changes were lost or modified"
}
`;
}
```

### Store Report in State

```javascript
// Update state with verification results
function updateStateWithVerification(verificationReport) {
  const state = loadState(".ttt/memory/ttt-nice-git-commits/state.json");

  state.flowSpecificData.verificationPassed = verificationReport.overallSuccess;
  state.flowSpecificData.verificationReport = {
    timestamp: verificationReport.timestamp,
    gitDiffPassed: verificationReport.gitDiff.success,
    buildPassed: verificationReport.build.success,
    testsPassed: verificationReport.tests.success,
  };

  // Mark verification step as completed
  const verifyStep = state.steps.find(
    (s) => s.name === "verify-commit-integrity",
  );
  verifyStep.status = "completed";
  verifyStep.completedAt = new Date().toISOString();

  // Update current step to next
  state.currentStep = state.currentStep + 1;
  const nextStep = state.steps.find((s) => s.id === state.currentStep);
  nextStep.status = "in-progress";
  nextStep.startedAt = new Date().toISOString();

  state.lastUpdatedAt = new Date().toISOString();

  saveState(".ttt/memory/ttt-nice-git-commits/state.json", state);
}
```

## Best Practices for AI Agents

### Never Skip Git Diff Check

```javascript
// This is THE critical verification
// ALWAYS run it, ALWAYS check result

const diffOutput = execSync("git diff backup/<branch> HEAD").toString();

if (diffOutput.trim().length === 0) {
  console.log("✓ Verification passed: No differences detected");
  return { success: true };
} else {
  console.error("✗ Verification FAILED: Differences detected");
  console.error("Diff output:", diffOutput);
  return { success: false, diff: diffOutput };
}
```

### Present Clear Results to User

```javascript
// Don't just say "verification passed"
// Show evidence

console.log(`
Verification Results:

✓ Git diff: No differences (all changes preserved)
✓ File count: 35 files in both (match)
✓ Build: Successful
✓ Tests: 127 tests passed
⚠ Linting: 3 warnings (non-critical)

Overall: SUCCESS - Safe to proceed
`);
```

### Handle Build/Test Failures Gracefully

```javascript
// Build/test failures are non-critical if git diff passes

if (!gitDiffPassed) {
  // CRITICAL - must restore
  offerImmediateRestore();
} else if (!buildPassed || !testsPassed) {
  // Non-critical - offer options
  console.warn("Changes preserved but build/tests failing");
  console.warn("This may indicate commit ordering issues");
  offerOptions(["restore", "continue", "adjust-order"]);
} else {
  // All good
  proceedToPresentation();
}
```

### Store All Verification Evidence

```javascript
// Save everything for user review
const artifacts = {
  "verification-results.txt": formatVerificationReport(results),
  "git-diff-output.txt": diffOutput,
  "build-output.txt": buildOutput,
  "test-output.txt": testOutput,
  "lint-output.txt": lintOutput,
};

for (const [filename, content] of Object.entries(artifacts)) {
  writeFile(`.ttt/memory/ttt-nice-git-commits/artifacts/${filename}`, content);
}
```

## Verification Checklist

### MANDATORY Verifications (Must Pass)

- [ ] `git diff backup/<branch> HEAD` produces empty output
- [ ] File count matches between backup and HEAD
- [ ] All files in backup are present in HEAD
- [ ] No unexpected files added

### RECOMMENDED Verifications (Should Pass)

- [ ] Build succeeds at HEAD
- [ ] Tests pass at HEAD
- [ ] Linting passes (or only warnings)
- [ ] No security vulnerabilities introduced

### INFORMATIONAL Checks

- [ ] Commit count (before vs after)
- [ ] Average files per commit (before vs after)
- [ ] Commit message quality (conventional format)
- [ ] Commit size distribution

## References

- **Main Skill**: [SKILL.md](SKILL.md)
- **State Management**: [state-management.md](state-management.md)
- **Presentation**: [presentation.md](presentation.md)
- **Troubleshooting Guide**: [resources/troubleshooting-guide.md](resources/troubleshooting-guide.md)
