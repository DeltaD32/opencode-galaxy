---
name: State Management
category: git-commit-reorganization
description: Persistent state tracking for resumable Git commit reorganization workflows
---

# State Management Skill

## Purpose

Provides persistent state tracking for Git commit reorganization workflows, enabling:

- Resumption after interruptions (session timeout, editor closure, crashes)
- Progress tracking across multi-step operations
- Artifact storage for analysis, plans, and verification results
- Safety through backup branch name persistence

## State Directory Structure

```
.ttt/memory/ttt-nice-git-commits/
├── state.json              # Main state file
└── artifacts/              # Workflow artifacts
    ├── commit-analysis.md          # Detailed commit analysis
    ├── atomic-commit-plan.md       # Planned atomic commits
    ├── verification-results.txt    # Git diff verification output
    └── commit-comparison.md        # Before/after comparison
```

## State File Schema

```json
{
  "flowName": "ttt-nice-git-commits",
  "startedAt": "2026-01-15T14:30:00Z",
  "lastUpdatedAt": "2026-01-15T14:45:00Z",
  "currentStep": 5,
  "totalSteps": 7,
  "steps": [
    {
      "id": 1,
      "name": "validate-clean-working-directory",
      "status": "completed",
      "completedAt": "2026-01-15T14:31:00Z"
    },
    {
      "id": 2,
      "name": "validate-prerequisites",
      "status": "completed",
      "completedAt": "2026-01-15T14:32:00Z"
    },
    {
      "id": 3,
      "name": "create-backup-branch",
      "status": "completed",
      "completedAt": "2026-01-15T14:33:00Z"
    },
    {
      "id": 4,
      "name": "analyze-commit-changes",
      "status": "completed",
      "completedAt": "2026-01-15T14:38:00Z"
    },
    {
      "id": 5,
      "name": "create-atomic-commits",
      "status": "in-progress",
      "startedAt": "2026-01-15T14:40:00Z"
    },
    {
      "id": 6,
      "name": "verify-commit-integrity",
      "status": "pending"
    },
    {
      "id": 7,
      "name": "present-results-user",
      "status": "pending"
    }
  ],
  "flowSpecificData": {
    "currentBranch": "feature/user-authentication",
    "backupBranch": "backup/feature-user-authentication-20260115-143000",
    "baseBranch": "main",
    "originalCommitCount": 3,
    "originalCommits": [
      {
        "hash": "abc123def",
        "message": "WIP: authentication work",
        "filesChanged": 15,
        "timestamp": "2026-01-14T10:20:00Z"
      },
      {
        "hash": "def456ghi",
        "message": "more updates",
        "filesChanged": 8,
        "timestamp": "2026-01-14T15:30:00Z"
      },
      {
        "hash": "ghi789jkl",
        "message": "final changes",
        "filesChanged": 12,
        "timestamp": "2026-01-15T09:15:00Z"
      }
    ],
    "plannedAtomicCommits": [
      {
        "type": "feat",
        "scope": "auth",
        "description": "add JWT token validation",
        "files": ["src/auth/jwt.js", "src/auth/validator.js"],
        "dependencies": []
      },
      {
        "type": "test",
        "scope": "auth",
        "description": "add JWT validation tests",
        "files": ["tests/auth/jwt.test.js"],
        "dependencies": [0]
      },
      {
        "type": "feat",
        "scope": "user",
        "description": "implement user login endpoint",
        "files": ["src/api/login.js", "src/routes/auth.js"],
        "dependencies": [0]
      }
    ],
    "newCommits": [
      {
        "hash": "mno234pqr",
        "message": "feat(auth): add JWT token validation",
        "filesChanged": 2,
        "timestamp": "2026-01-15T14:41:00Z"
      },
      {
        "hash": "pqr567stu",
        "message": "test(auth): add JWT validation tests",
        "filesChanged": 1,
        "timestamp": "2026-01-15T14:43:00Z"
      }
    ],
    "verificationPassed": false
  }
}
```

## Initialization Protocol

### First Run (No Existing State)

```bash
# Check for existing state
if [ ! -f .ttt/memory/ttt-nice-git-commits/state.json ]; then
  # Create state directory
  mkdir -p .ttt/memory/ttt-nice-git-commits/artifacts

  # Initialize state.json
  # (Create with initial structure)
fi
```

### Resumption (Existing State Found)

**Present Options to User**:

```markdown
I found a previous commit reorganization session in progress.

**Current State**:

- Branch: feature/user-authentication
- Backup: backup/feature-user-authentication-20260115-143000
- Progress: Step 5 of 7 (Create Atomic Commits)
- Commits Created: 2 of 8 planned

**Options**:
(A) Resume from where we left off (Step 5: Create Atomic Commits)
(B) Start from scratch (restore from backup and begin fresh)

What would you like to do?
```

**Handle User Choice**:

**(A) Resume**:

1. Load state from `state.json`
2. Verify backup branch still exists: `git branch | grep backup/<branch>`
3. If backup missing: **ABORT** - Cannot proceed without restoration capability
4. Load `flowSpecificData` to understand context
5. Continue from `currentStep` (or first "pending" or "in-progress" step)
6. Use `newCommits[]` to understand what's already done

**(B) Start Fresh**:

1. Restore from backup: `git reset --hard backup/<branch>`
2. Delete state directory: `rm -rf .ttt/memory/ttt-nice-git-commits/`
3. Verify restoration: `git status`, `git log`
4. Initialize fresh state
5. Proceed from Step 1

## State Update Protocol

### After Each Step Completion

```javascript
// Example: After completing "create-backup-branch" step
{
  // Update step status
  steps[2].status = "completed";
  steps[2].completedAt = getCurrentTimestamp();

  // Update current step pointer
  currentStep = 4; // Move to next step

  // Mark next step as in-progress
  steps[3].status = "in-progress";
  steps[3].startedAt = getCurrentTimestamp();

  // Update lastUpdatedAt
  lastUpdatedAt = getCurrentTimestamp();

  // Store step-specific data
  flowSpecificData.backupBranch = "backup/feature-user-auth-20260115-143000";

  // Write to disk IMMEDIATELY
  writeStateFile();
}
```

### During Atomic Commit Creation

**CRITICAL**: Update state after EACH commit is created:

```javascript
// After creating each atomic commit
{
  // Add new commit to array
  flowSpecificData.newCommits.push({
    hash: getCommitHash("HEAD"),
    message: conventionalCommitMessage,
    filesChanged: fileCount,
    timestamp: getCurrentTimestamp(),
  });

  // Update lastUpdatedAt
  lastUpdatedAt = getCurrentTimestamp();

  // Write to disk IMMEDIATELY
  writeStateFile();
}
```

This enables resumption even if interrupted mid-commit-creation.

### On Interruption

If process is interrupted (timeout, crash, user abort):

1. **DO NOT** delete state directory
2. **DO NOT** delete backup branch
3. State remains with last successful update
4. Mark current step as "interrupted" (if detection possible)
5. On next invocation, offer resumption

## Artifact Storage

### commit-analysis.md

Store detailed analysis of original commits:

```markdown
# Commit Analysis

## Original Commits

### Commit 1: abc123def

**Message**: WIP: authentication work
**Files Changed**: 15
**Timestamp**: 2026-01-14T10:20:00Z

**File Categories**:

- Auth Core: src/auth/jwt.js, src/auth/validator.js
- User Management: src/models/user.js, src/api/users.js
- Configuration: config/auth.config.js
- Tests: tests/auth/jwt.test.js, tests/models/user.test.js
- Documentation: docs/api/auth.md

...
```

### atomic-commit-plan.md

Store planned atomic commit structure:

```markdown
# Atomic Commit Plan

## Commit 1: feat(auth): add JWT token validation

**Files**: src/auth/jwt.js, src/auth/validator.js
**Dependencies**: None
**Rationale**: Core authentication logic, no external dependencies

## Commit 2: test(auth): add JWT validation tests

**Files**: tests/auth/jwt.test.js
**Dependencies**: Commit 1 (tests require implementation)
**Rationale**: Tests for JWT validation logic

...
```

### verification-results.txt

Store git diff output:

```bash
# Empty output indicates success
# Any output indicates differences between backup and HEAD
```

### commit-comparison.md

Store before/after comparison for user review:

```markdown
# Commit Comparison

## Before

- 3 commits
- Generic messages ("WIP", "updates", "fixes")
- Average 11.7 files per commit

### Commit Messages

1. WIP: authentication work (15 files)
2. more updates (8 files)
3. final changes (12 files)

## After

- 8 commits
- Conventional commit messages
- Average 2.3 files per commit

### Commit Messages

1. feat(auth): add JWT token validation (2 files)
2. test(auth): add JWT validation tests (1 file)
3. feat(user): implement user login endpoint (3 files)
   ...
```

## State-Specific Considerations

### CRITICAL State Elements

**MUST be preserved**:

- `backupBranch`: Without this, restoration is impossible
- `originalCommits[]`: Needed to verify all changes preserved
- `newCommits[]`: Tracks partial progress for resumption

**MUST be verified on resumption**:

- Backup branch still exists: `git branch | grep backup/<branch>`
- If missing: **ABORT** and warn user

### State Transitions

```
Initial → Validating → Backup Created → Analyzing →
Creating Commits → Verifying → Presenting → Complete
```

Each transition:

1. Updates step status
2. Stores step-specific data
3. Writes state to disk
4. Enables rollback to previous step if needed

## Error Handling

### State File Corruption

If `state.json` cannot be parsed:

1. Look for backup branch (search git branches for `backup/`)
2. If found: Offer restoration
3. If not found: **ABORT** - Cannot safely proceed
4. Log error, suggest manual intervention

### Missing Backup Branch

If state indicates backup but branch doesn't exist:

1. **ABORT IMMEDIATELY**
2. Warn user: "Cannot proceed - backup branch missing"
3. Suggest manual restoration or starting fresh
4. **NEVER** proceed with destructive operations

### Partial State

If state shows "in-progress" step with incomplete data:

1. Review `newCommits[]` to see what's already done
2. Verify those commits exist: `git log`
3. If commits missing: Restore from backup and restart
4. If commits exist: Resume from next uncommitted change

## Best Practices for AI Agents

### Always Start with State Check

```javascript
// First thing in workflow
const stateExists = checkForStateFile();

if (stateExists) {
  const state = loadState();
  presentResumeOrRestartOptions(state);
  await getUserChoice();
} else {
  initializeFreshState();
  proceedWithWorkflow();
}
```

### Update State Continuously

```javascript
// After EACH atomic commit
createAtomicCommit(files, message);
updateStateWithNewCommit(commitHash, message, files);
writeStateToDisk(); // CRITICAL - Enables resumption
```

### Verify Backup Before Destructive Ops

```javascript
// Before ANY git reset operation
const backupExists = verifyBackupBranch(state.backupBranch);

if (!backupExists) {
  abortWorkflow("Backup branch missing - cannot proceed safely");
  return;
}

// Proceed with reset
gitReset();
```

### Clean Up Appropriately

**On successful completion with user approval**:

```bash
# Delete backup branch
git branch -D backup/<branch>

# Ask user about state directory
"Would you like to keep the workflow state for reference? (Y/N)"
# If No: rm -rf .ttt/memory/ttt-nice-git-commits/
```

**On user rejection**:

```bash
# Restore from backup
git reset --hard backup/<branch>

# Delete state directory
rm -rf .ttt/memory/ttt-nice-git-commits/

# Keep backup branch for user's manual use
```

**On interruption**:

```bash
# Keep everything intact
# State directory remains for resumption
# Backup branch remains for restoration
```

## State Lifecycle

```
1. Initialize → Create state directory and state.json
2. Execute Steps → Update state after each step completion
3. Store Artifacts → Save analysis, plans, results
4. Complete → Mark all steps complete, verification passed
5. User Approval → Await user decision
6. Cleanup → Delete backup (if approved) and optionally state directory
```

## References

- **Main Skill**: [SKILL.md](SKILL.md)
- **Agent Prompt**: [../../agents/nice-git-commits.agent.md](../../agents/nice-git-commits.agent.md)
- **Flow Documentation**: [../../flows/nice-git-commits.md](../../flows/nice-git-commits.md)
