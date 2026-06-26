---
name: git-commit-reorganization
description: Transform messy commit history into clean, atomic commits with proper conventional commit messages through analysis, planning, and safe reorganization.
license: Proprietary
compatibility: Requires Git 2.23 or higher, clean working directory (no uncommitted changes), and local branch (not yet pushed, or force-push acceptable)
metadata:
  author: Matthias Bilger <matthias.bilger@bmw.de>
  version: "1.0.0"
  tags:
    - git
    - version-control
    - commit-management
    - conventional-commits
    - code-quality
---

# Git Commit Reorganization

## Purpose

This skill helps reorganize messy Git commit history into clean, atomic commits with proper conventional commit messages. It analyzes existing commits, plans a better structure, and safely reorganizes the history while preserving all changes.

## When to Use

Use this skill when:

- Commits have generic messages like "WIP", "updates", "fixes"
- Large commits mix multiple unrelated changes
- Commit history needs cleanup before code review or merge
- User asks to "organize commits", "split commits", or "clean up history"
- Feature branch needs better structure for maintainability

## Workflow

### 1. Create Safety Backup

Before any destructive operations, create a backup branch:

```bash
git branch backup/<branch-name>-$(date +%Y%m%d-%H%M%S)
```

This provides instant restoration capability if needed:

```bash
git reset --hard backup/<branch-name>-<timestamp>
```

### 2. Analyze Existing Commits

Analyze the commit history to understand what changes were made and how they should be grouped. See [references/commit-analysis.md](references/commit-analysis.md) for detailed guidance.

**Key activities:**

- List all commits since base branch
- Extract file changes from each commit
- Group related files logically (e.g., tests with implementations)
- Detect dependencies between changes
- Check for existing gitlint configuration (`.gitlint`, `pyproject.toml`, `.git/hooks/commit-msg`)
- Understand repository's commit message conventions
- Plan atomic commit structure

**Output:** A commit plan showing proposed atomic commits with:

- Commit type and optional scope (following gitlint rules)
- Descriptive commit message (max 70 characters)
- List of files included
- Rationale for grouping

### 3. Create Atomic Commits

Execute the planned reorganization by creating new atomic commits. See [references/atomic-commit-creation.md](references/atomic-commit-creation.md) for detailed guidance.

**Key activities:**

- Reset to base branch (preserving changes): `git reset --soft <base-branch>`
- Stage files for each planned commit: `git add <files>`
- Create commit with properly formatted message following gitlint rules
- **Run test suite after each commit**: Ensure tests pass for every commit
- Repeat for each planned commit

**Test Verification (Required):**

After creating each commit, run the repository's test suite to ensure the commit doesn't break any tests. This ensures each commit is independently valid and the history is bisectable.

**If test command is unclear:**

- Check for common test commands: `npm test`, `pytest`, `uv run pytest`, `make test`, `./gradlew test`
- Look for test scripts in `package.json`, `Makefile`, `pyproject.toml`, or CI configuration
- **Ask the user to provide the test command** if it cannot be determined automatically

**If tests fail for a commit:**

- The commit grouping may be incorrect (files that depend on each other are split)
- Adjust the commit plan to group dependent changes together
- Re-create the commit with the corrected file grouping
- Re-run tests to verify

**Commit Message Format:**

Respect existing gitlint rules if present in the repository. If no gitlint configuration exists, follow these rules:

1. **Prefix**: Use one of: `fix`, `feat`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `revert`, `ci`, `build`
2. **Title length**: Maximum 70 characters
3. **Format**: `type(scope): description` or `type: description`
4. **Body separation**: If adding a body, separate it from the title with a blank line

**Examples:**

```bash
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix: resolve race condition in data loader"
git commit -m "docs: update API documentation" -m "" -m "Add examples for new endpoints"
```

**Important:** Each commit should be self-contained and represent a single logical change.

### 4. Verify Integrity

Ensure no changes were lost during reorganization. See [references/verification.md](references/verification.md) for detailed guidance.

**Required verification:**

```bash
git diff backup/<branch-name>-<timestamp> HEAD
```

Output must be empty. Any differences indicate changes were lost or modified.

**Additional required verification:**

- **Run test suite**: Ensure all tests pass on the final HEAD (tests should have passed for each individual commit already)
- **Run build** (if applicable): Ensure project still compiles
- **Verify each commit**: Each should be atomic, buildable, and have passing tests

### 5. Present Results

Show the user what changed and get approval. See [references/presentation.md](references/presentation.md) for detailed guidance.

**Present:**

- Before/after commit comparison
- Example of old vs new commit messages
- Verification results (diff, build, tests)
- Instructions for restoration if needed

**Offer options:**

1. **Approve**: Keep new commits, optionally delete backup
2. **Reject**: Restore from backup branch
3. **Keep both**: Preserve both backup and new commits for comparison

## Safety Features

### Backup Branch

Always create backup before destructive operations. Store backup branch name for restoration.

### Verification

Always verify no changes were lost:

- Compare backup to HEAD (must be identical)
- Run build if applicable
- Run tests if applicable

### User Approval

Never finalize without user approval. Provide clear restoration instructions.

## Common Patterns

### Pattern 1: Clean Feature Branch Before PR

1. User completes feature with messy commits
2. Agent suggests reorganizing commits
3. Create backup branch
4. Analyze commits and plan atomic structure
5. Create new atomic commits
6. Verify integrity
7. Present results and get approval
8. Create PR with clean history

### Pattern 2: Rollback on Verification Failure

1. Complete atomic commit creation
2. Run verification: `git diff backup/<branch> HEAD`
3. Verification shows differences
4. Alert user immediately
5. Restore from backup: `git reset --hard backup/<branch>`
6. Analyze what went wrong, suggest manual approach

## Inputs

- **Base branch**: The branch to compare against (e.g., `main`, `develop`)
- **Current branch**: The branch with messy commits to reorganize
- **Commit range** (optional): Specific commits to reorganize (default: all commits since base)
- **Test command**: Command to run test suite (e.g., `npm test`, `pytest`) - ask user if unclear

## Outputs

- **Backup branch**: Safety backup of original history
- **Reorganized commits**: Clean, atomic commits with conventional messages
- **Verification report**: Proof that no changes were lost
- **Before/after comparison**: Visual representation of improvements

## Error Handling

### Critical Errors (Stop Immediately)

- **Dirty working directory**: Uncommitted changes present
- **No backup branch**: Cannot proceed without restoration capability
- **Verification failed**: Changes lost or modified during reorganization

**Action**: Stop immediately, restore from backup if operations started, report error to user

### Recoverable Errors

- **Commit message validation failed**: Message doesn't meet gitlint rules (wrong prefix, too long, etc.) - ask user for better message or auto-correct if possible
- **Build fails at intermediate commit**: Adjust commit order or grouping
- **Tests fail at intermediate commit**: Adjust commit plan to group dependent changes together
- **Merge conflict during reorganization**: Resolve interactively with user

**Action**: Pause, interact with user, adjust plan, continue

### Warnings

- **Large number of commits**: May take significant time
- **Complex file dependencies**: May require manual review of commit order
- **Force push required**: User must understand implications

**Action**: Warn user, explain implications, proceed with confirmation

## References

For detailed guidance on specific aspects:

- **[Commit Analysis](references/commit-analysis.md)** - How to analyze commits and plan atomic structure
- **[Atomic Commit Creation](references/atomic-commit-creation.md)** - How to create atomic commits safely
- **[Verification](references/verification.md)** - How to verify integrity after reorganization
- **[Presentation](references/presentation.md)** - How to present results and get user approval
- **[State Management](references/state-management.md)** - Optional state tracking for complex reorganizations

## External Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/) - Commit message format
- [Git Documentation](https://git-scm.com/doc) - Git command reference
- [Gitlint Documentation](https://jorisroovers.com/gitlint/) - Commit message linting tool
