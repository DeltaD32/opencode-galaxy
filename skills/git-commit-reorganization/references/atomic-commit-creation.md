---
name: Atomic Commit Creation
category: git-commit-reorganization
description: Step-by-step creation of clean, atomic commits from planned structure with progressive state persistence for resumability
---

# Atomic Commit Creation Skill

## Purpose

Creates clean, atomic commits following the planned structure by:

- Safely resetting to base branch while preserving changes
- Staging specific files for each atomic commit
- Creating commits with conventional messages
- Updating state progressively for resumability

## Creation Process

### Step 1: Prepare for Commit Creation

**Verify prerequisites**:

```bash
# Verify backup branch exists
git branch | grep backup/<branch-name>

# Verify current branch state
git status

# Verify clean working directory
git diff --quiet && git diff --cached --quiet
```

**Critical safety checks**:

- Backup branch MUST exist
- Working directory MUST be clean
- State file MUST contain backup branch name

### Step 2: Reset to Base Branch (Preserve Changes)

**CRITICAL**: Use `--soft` to preserve changes in staging area:

```bash
# Get current branch name
CURRENT_BRANCH=$(git branch --show-current)

# Get base branch from state
BASE_BRANCH="main"  # or from .ttt/memory/ttt-nice-git-commits/state.json

# Find common ancestor
MERGE_BASE=$(git merge-base HEAD $BASE_BRANCH)

# Reset to base branch, keeping changes STAGED
git reset --soft $MERGE_BASE
```

**Why `--soft`**:

- `--soft`: Moves HEAD, keeps changes STAGED (✅ correct)
- `--mixed`: Moves HEAD, keeps changes UNSTAGED (⚠️ also works but requires re-staging)
- `--hard`: Moves HEAD, **DISCARDS CHANGES** (❌ NEVER USE HERE)

**After reset, verify changes are preserved**:

```bash
# Should show all changes from original commits
git diff --cached --stat

# Should list all modified files
git diff --cached --name-only
```

### Step 3: Unstage All Changes

**Prepare for selective staging**:

```bash
# Unstage everything (using mixed reset to current HEAD)
git reset HEAD

# Verify nothing is staged
git diff --cached --stat  # Should show nothing

# Verify all changes are still present (unstaged)
git diff --stat  # Should show all changes
```

Now all changes are in working directory, ready for selective staging.

### Step 4: Create Atomic Commits

**For each planned commit** (from commit analysis):

```javascript
// Example: Creating first atomic commit
const commit = atomicCommitPlan[0];

// 1. Stage only the relevant files
for (const file of commit.files) {
  execSync(`git add "${file}"`);
}

// 2. Verify staging
const stagedFiles = execSync("git diff --cached --name-only")
  .toString()
  .trim()
  .split("\n");
console.log(`Staged ${stagedFiles.length} files for commit`);

// 3. Create commit with conventional message
const message = `${commit.type}(${commit.scope || ""}): ${commit.description}`;
execSync(`git commit -m "${message}"`);

// 4. Capture commit hash
const commitHash = execSync("git rev-parse HEAD").toString().trim();

// 5. Update state IMMEDIATELY
state.flowSpecificData.newCommits.push({
  hash: commitHash,
  message: message,
  filesChanged: commit.files.length,
  timestamp: new Date().toISOString(),
});
saveState(state);

// 6. Continue to next commit
```

**Progressive state updates enable resumption**:

- If interrupted after commit 3 of 10, can resume from commit 4
- State file tracks which commits are already created
- Backup branch enables rollback if needed

### Step 5: Handle File Staging Edge Cases

**Partial file changes** (if needed):

```bash
# Interactive staging for specific hunks
git add -p <file>

# Review hunks:
# y = stage this hunk
# n = skip this hunk
# s = split hunk into smaller parts
# q = quit
```

**New files**:

```bash
# Stage new files explicitly
git add <new-file>
```

**Deleted files**:

```bash
# Stage deletions
git add <deleted-file>
# or
git rm <deleted-file>
```

**Renamed files**:

```bash
# Git auto-detects renames if >50% similarity
git add <old-name> <new-name>

# Verify rename detected
git status  # Should show "renamed: old-name -> new-name"
```

### Step 6: Verify Each Commit

**After creating each commit**:

```bash
# Verify commit was created
git log -1 --oneline

# Verify correct files are in commit
git show HEAD --name-only

# Verify commit message format
git log -1 --format=%s | grep -E '^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\([a-z0-9-]+\))?: .+'
```

**If verification fails**:

- Amend commit: `git commit --amend`
- Or reset: `git reset --soft HEAD~1`, adjust, recommit

## Commit Message Formatting

### Conventional Commit Structure

```
type(scope): short description

[optional body]

[optional footer]
```

### Type Selection

```javascript
const typeGuide = {
  feat: "New feature or functionality",
  fix: "Bug fix",
  docs: "Documentation only changes",
  style: "Code style (formatting, missing semicolons, etc.)",
  refactor: "Code restructuring without functional changes",
  perf: "Performance improvements",
  test: "Adding or updating tests",
  chore: "Maintenance tasks (dependencies, tooling, config)",
  ci: "CI/CD pipeline changes",
  build: "Build system changes",
};
```

### Scope Guidelines

```javascript
// Good scopes (specific, consistent)
"auth"; // Authentication module
"user"; // User management
"api"; // API endpoints
"ui"; // User interface
"config"; // Configuration

// Avoid (too generic or inconsistent)
"stuff"; // Too vague
"Auth"; // Should be lowercase
"authentication-and-authorization"; // Too long
```

### Description Guidelines

```javascript
// Good descriptions (imperative, clear, concise)
"add JWT token validation";
"implement user login endpoint";
"fix password reset email template";
"update API documentation for auth endpoints";

// Avoid
"Added JWT validation"; // Past tense (use imperative)
"Updates"; // Too generic
"Fix bug"; // Not specific enough
"IMPLEMENT USER LOGIN"; // Should be lowercase
"Add the JWT token validation logic and middleware."; // Has period (omit)
```

### Message Examples

**Simple commit**:

```
feat(auth): add JWT token validation
```

**With body**:

```
feat(auth): add JWT token validation

Implement JWT token validation middleware with signature
verification and expiration checking.
```

**With body and footer**:

```
feat(auth): add JWT token validation

Implement JWT token validation middleware with signature
verification and expiration checking.

- Add JwtValidator class with validation logic
- Add unit tests for token validation
- Update auth middleware to use validator

Closes #234
```

**Breaking change**:

```
feat(auth): change authentication token format

BREAKING CHANGE: Authentication tokens now use JWT format
instead of opaque tokens. Clients must update to handle JWT.
```

## State Management Integration

### Update State After Each Commit

```javascript
// After creating each atomic commit
function updateStateAfterCommit(commitData) {
  // Load current state
  const state = loadState(".ttt/memory/ttt-nice-git-commits/state.json");

  // Add new commit to tracking array
  state.flowSpecificData.newCommits.push({
    hash: commitData.hash,
    message: commitData.message,
    filesChanged: commitData.files.length,
    timestamp: new Date().toISOString(),
  });

  // Update last updated timestamp
  state.lastUpdatedAt = new Date().toISOString();

  // Write to disk IMMEDIATELY
  saveState(".ttt/memory/ttt-nice-git-commits/state.json", state);
}
```

### Resume from Partial Completion

```javascript
// When resuming after interruption
function resumeCommitCreation() {
  // Load state
  const state = loadState(".ttt/memory/ttt-nice-git-commits/state.json");

  // Get commits already created
  const completedCommits = state.flowSpecificData.newCommits.length;

  // Get total planned commits
  const totalCommits = state.flowSpecificData.plannedAtomicCommits.length;

  console.log(
    `Resuming: ${completedCommits}/${totalCommits} commits already created`,
  );

  // Continue from next commit
  for (let i = completedCommits; i < totalCommits; i++) {
    const commit = state.flowSpecificData.plannedAtomicCommits[i];
    createAtomicCommit(commit);
    updateStateAfterCommit({ ...commit, hash: getLastCommitHash() });
  }
}
```

## Error Handling

### Staging Fails (File Not Found)

```bash
# If file doesn't exist
error: pathspec 'src/missing-file.js' did not match any files
```

**Resolution**:

1. Check if file was deleted in another commit
2. Verify file path is correct
3. Update commit plan to remove missing file
4. Continue with remaining files

### Commit Fails (Empty Commit)

```bash
# If no files staged
nothing to commit
```

**Resolution**:

1. Verify files were staged: `git diff --cached`
2. Check if files were already committed
3. Skip this commit if all files already committed
4. Adjust remaining commit plan

### Merge Conflict During Staging

```bash
# If file has conflicts
error: Merge conflict in src/file.js
```

**Resolution**:

1. This shouldn't happen during commit splitting
2. Indicates working directory wasn't clean at start
3. **ABORT** immediately
4. Restore from backup: `git reset --hard backup/<branch>`
5. Investigate why conflict occurred

### Build Breaks at Intermediate Commit

**Detection**:

```bash
# Run build after each commit (if applicable)
npm run build  # or project-specific build command
```

**Resolution**:

1. If build fails, commit order may be wrong
2. Check dependencies: does this commit require another commit first?
3. Options:
   - Reorder commits (if dependencies allow)
   - Combine commits to maintain buildability
   - Accept temporary build break (document why)

## Best Practices for AI Agents

### Always Verify Backup First

```javascript
// BEFORE any git reset
function verifyBackupExists(backupBranch) {
  try {
    execSync(`git rev-parse --verify ${backupBranch}`);
    return true;
  } catch {
    console.error("CRITICAL: Backup branch not found!");
    return false;
  }
}

if (!verifyBackupExists(state.flowSpecificData.backupBranch)) {
  throw new Error("Cannot proceed without backup branch");
}
```

### Update State Continuously

```javascript
// Don't batch state updates - do after EACH commit
for (const commit of plannedCommits) {
  createCommit(commit);
  updateState(commit); // ← CRITICAL for resumability

  // NOT like this:
  // createAllCommits()
  // updateStateOnce()  // ← Would lose partial progress
}
```

### Validate Commit Messages

```javascript
// Ensure conventional commit format
function validateCommitMessage(type, scope, description) {
  // Check type
  const validTypes = [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "chore",
    "ci",
    "build",
  ];
  if (!validTypes.includes(type)) {
    throw new Error(`Invalid type: ${type}`);
  }

  // Check scope (optional but if present, must be lowercase alphanumeric)
  if (scope && !/^[a-z0-9-]+$/.test(scope)) {
    throw new Error(`Invalid scope: ${scope}`);
  }

  // Check description
  if (description.length === 0) {
    throw new Error("Description cannot be empty");
  }
  if (description.length > 72) {
    console.warn(`Description too long (${description.length} chars, max 72)`);
  }
  if (description[0] === description[0].toUpperCase()) {
    console.warn("Description should start with lowercase");
  }
  if (description.endsWith(".")) {
    console.warn("Description should not end with period");
  }

  return true;
}
```

### Test Build After Completion

```javascript
// After all commits created
async function verifyBuildWorks() {
  console.log("Verifying build...");

  try {
    // Read build command from project config
    const projectTools = readFile(".ttt/config/project-tools.md");
    const buildCommand = extractBuildCommand(projectTools);

    // Run build
    execSync(buildCommand, { stdio: "inherit" });
    console.log("✓ Build successful");
    return true;
  } catch (error) {
    console.error("✗ Build failed");
    console.error("Consider reordering commits to maintain buildability");
    return false;
  }
}
```

## Commit Creation Workflow

```
1. Verify Prerequisites
   ├─ Backup branch exists
   ├─ Working directory clean
   └─ State file valid

2. Reset to Base (--soft)
   ├─ Find merge base
   ├─ Reset preserving changes
   └─ Verify changes staged

3. Unstage All Changes
   ├─ Reset HEAD (mixed)
   └─ Verify changes in working directory

4. For Each Planned Commit:
   ├─ Stage specific files
   ├─ Verify staging
   ├─ Create commit with conventional message
   ├─ Capture commit hash
   ├─ Update state immediately
   └─ Continue to next

5. Verify All Commits Created
   ├─ Check commit count
   ├─ Verify all files committed
   └─ Test build (optional)

6. Proceed to Verification Step
```

## References

- **Main Skill**: [SKILL.md](SKILL.md)
- **State Management**: [state-management.md](state-management.md)
- **Commit Analysis**: [commit-analysis.md](commit-analysis.md)
- **Verification**: [verification.md](verification.md)
- **Conventional Commits Guide**: [resources/conventional-commits-guide.md](resources/conventional-commits-guide.md)
- **Git Commands Reference**: [resources/git-commands-reference.md](resources/git-commands-reference.md)
