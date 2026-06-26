---
name: Commit Analysis
category: git-commit-reorganization
description: Intelligent analysis of existing commits to plan atomic reorganization with logical groupings and conventional commit messages
---

# Commit Analysis Skill

## Purpose

Analyzes existing Git commits to plan atomic reorganization by:

- Examining file changes and identifying logical groupings
- Detecting dependencies between changes (e.g., tests depend on implementation)
- Planning conventional commit messages
- Creating user-reviewable commit plan

## Analysis Process

### Step 1: Gather Commit Information

**Collect data from existing commits**:

```bash
# Get commit history from base branch to HEAD
git log main..HEAD --oneline

# For each commit, get detailed information
git show <commit-hash> --stat --name-only

# Get complete file diff for analysis
git diff main..HEAD --name-status
```

**Data to capture**:

- Commit hash
- Commit message
- Files changed (added, modified, deleted)
- Timestamp
- Author (for context)
- Line changes per file

### Step 2: Categorize File Changes

**Group files by logical concern**:

```javascript
// Example categorization
const fileCategories = {
  authCore: [
    "src/auth/jwt.js",
    "src/auth/validator.js",
    "src/auth/middleware.js",
  ],
  userManagement: [
    "src/models/user.js",
    "src/api/users.js",
    "src/services/userService.js",
  ],
  configuration: ["config/auth.config.js", "config/database.config.js"],
  tests: [
    "tests/auth/jwt.test.js",
    "tests/models/user.test.js",
    "tests/api/users.test.js",
  ],
  documentation: ["docs/api/auth.md", "docs/setup.md", "README.md"],
};
```

**Categorization strategies**:

1. **By directory structure**: Group files in same directory
2. **By functionality**: Group related features (auth, user, api)
3. **By type**: Group by role (implementation, tests, docs, config)
4. **By dependencies**: Keep dependent changes together

### Step 3: Detect Dependencies

**Identify dependency relationships**:

```javascript
// Example dependency detection
const dependencies = {
  "tests/auth/jwt.test.js": ["src/auth/jwt.js"], // Tests depend on implementation
  "src/api/users.js": ["src/models/user.js"], // API depends on model
  "docs/api/auth.md": ["src/auth/jwt.js"], // Docs reference implementation
};
```

**Dependency rules**:

- **Tests** always depend on implementation
- **Documentation** typically depends on implementation
- **API routes** depend on controllers/services
- **Controllers/Services** depend on models
- **Configuration** typically has no dependencies (can be first)

### Step 4: Plan Atomic Commits

**Create logical commit structure**:

```javascript
// Example commit plan
const atomicCommitPlan = [
  {
    order: 1,
    type: "chore",
    scope: "config",
    description: "add authentication configuration",
    files: ["config/auth.config.js"],
    dependencies: [],
    rationale: "Configuration needed by auth logic",
  },
  {
    order: 2,
    type: "feat",
    scope: "auth",
    description: "add JWT token validation",
    files: [
      "src/auth/jwt.js",
      "src/auth/validator.js",
      "src/auth/middleware.js",
    ],
    dependencies: [1],
    rationale: "Core authentication functionality",
  },
  {
    order: 3,
    type: "test",
    scope: "auth",
    description: "add JWT validation tests",
    files: ["tests/auth/jwt.test.js"],
    dependencies: [2],
    rationale: "Tests require JWT implementation",
  },
  {
    order: 4,
    type: "feat",
    scope: "user",
    description: "implement user model and service",
    files: ["src/models/user.js", "src/services/userService.js"],
    dependencies: [1],
    rationale: "User management foundation",
  },
  {
    order: 5,
    type: "feat",
    scope: "api",
    description: "add user management endpoints",
    files: ["src/api/users.js"],
    dependencies: [2, 4],
    rationale: "API depends on auth middleware and user model",
  },
  {
    order: 6,
    type: "test",
    scope: "user",
    description: "add user model and API tests",
    files: ["tests/models/user.test.js", "tests/api/users.test.js"],
    dependencies: [4, 5],
    rationale: "Tests require user implementation",
  },
  {
    order: 7,
    type: "docs",
    scope: "api",
    description: "document authentication API endpoints",
    files: ["docs/api/auth.md"],
    dependencies: [2, 5],
    rationale: "Documentation references implemented features",
  },
  {
    order: 8,
    type: "docs",
    scope: null,
    description: "update README with authentication setup",
    files: ["README.md", "docs/setup.md"],
    dependencies: [1, 2],
    rationale: "Setup guide references configuration and auth",
  },
];
```

### Step 5: Generate Conventional Commit Messages

**Format**: `type(scope): description`

**Type selection criteria**:

- `feat`: New features, functionality, capabilities
- `fix`: Bug fixes
- `refactor`: Code restructuring without functional changes
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `docs`: Documentation only changes
- `style`: Code formatting, whitespace, linting
- `chore`: Build tools, dependencies, configuration
- `ci`: CI/CD pipeline changes
- `build`: Build system changes

**Scope selection**:

- Use component/module name (e.g., `auth`, `user`, `api`)
- Keep scope consistent across related commits
- Omit scope if change is global (e.g., README update)

**Description rules**:

- Use imperative mood: "add feature" not "added feature"
- Start with lowercase
- No period at end
- Under 72 characters
- Be specific and descriptive

### Step 6: Validate Commit Plan

**Check for issues**:

```javascript
// Validation checks
const validationRules = [
  {
    rule: "Each file appears exactly once",
    check: (plan) => {
      const allFiles = plan.flatMap((c) => c.files);
      return allFiles.length === new Set(allFiles).size;
    },
  },
  {
    rule: "Dependencies are ordered correctly",
    check: (plan) => {
      for (const commit of plan) {
        for (const dep of commit.dependencies) {
          if (dep >= commit.order) return false;
        }
      }
      return true;
    },
  },
  {
    rule: "Commit messages follow conventional format",
    check: (plan) => {
      const conventionalPattern =
        /^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\([a-z]+\))?: .+$/;
      return plan.every((c) =>
        conventionalPattern.test(`${c.type}(${c.scope}): ${c.description}`),
      );
    },
  },
  {
    rule: "Each commit has at least one file",
    check: (plan) => plan.every((c) => c.files.length > 0),
  },
  {
    rule: "All commits have clear rationale",
    check: (plan) => plan.every((c) => c.rationale && c.rationale.length > 10),
  },
];
```

**If validation fails**:

- Report specific issue to user
- Adjust plan to resolve issue
- Re-validate before proceeding

## Project Context Integration

### Read Project Configuration

**MUST read before planning**:

```javascript
// Read project conventions
const projectSetup = readFile(".ttt/config/project-setup.md");
const projectTools = readFile(".ttt/config/project-tools.md");

// Extract relevant information
const conventionPreferences = {
  commitMessageFormat: projectSetup.conventionalCommitFormat,
  preferredScopes: projectSetup.preferredScopes,
  testingStrategy: projectTools.testFramework,
};
```

**Use project conventions**:

- Respect preferred commit scopes
- Follow project's commit message style
- Understand test organization (unit/integration/e2e)
- Recognize project-specific file patterns

### Adapt to Project Structure

**Frontend project patterns**:

```
src/components/     → scope: component name
src/pages/          → scope: page name
src/services/       → scope: "api" or service name
src/utils/          → scope: "utils" or function category
tests/              → type: "test", scope: matches implementation
```

**Backend project patterns**:

```
src/models/         → scope: "model" or model name
src/controllers/    → scope: "api" or "controller"
src/services/       → scope: service name
src/middleware/     → scope: "middleware" or function name
tests/              → type: "test", scope: matches implementation
```

**Fullstack project patterns**:

```
client/             → scope: component or page
server/             → scope: API or service
shared/             → scope: "shared" or "common"
docs/               → type: "docs", scope: document category
```

## Common Patterns

### Pattern 1: Feature with Tests

```
1. feat(feature): implement feature logic
2. test(feature): add feature tests
```

### Pattern 2: Refactor with Tests

```
1. refactor(module): extract helper functions
2. test(module): update tests for refactored code
```

### Pattern 3: Configuration → Implementation → Tests → Documentation

```
1. chore(config): add feature configuration
2. feat(feature): implement feature
3. test(feature): add feature tests
4. docs(feature): document feature usage
```

### Pattern 4: Model → Service → API → Tests

```
1. feat(model): add data model
2. feat(service): add business logic service
3. feat(api): add API endpoints
4. test(api): add API integration tests
```

## Presenting Plan to User

### Format for User Review

```markdown
# Proposed Atomic Commit Plan

## Summary

- **Original**: 3 commits with generic messages, 35 files total
- **Proposed**: 8 atomic commits with conventional messages
- **Average files per commit**: Before: 11.7 → After: 4.4

## Commit Breakdown

### 1. chore(config): add authentication configuration

**Files** (1):

- config/auth.config.js

**Rationale**: Configuration needed by auth logic

**Dependencies**: None

---

### 2. feat(auth): add JWT token validation

**Files** (3):

- src/auth/jwt.js
- src/auth/validator.js
- src/auth/middleware.js

**Rationale**: Core authentication functionality

**Dependencies**: Commit 1 (requires auth configuration)

---

### 3. test(auth): add JWT validation tests

**Files** (1):

- tests/auth/jwt.test.js

**Rationale**: Tests require JWT implementation

**Dependencies**: Commit 2 (tests require implementation)

---

[... continue for all commits ...]

## Questions for Review

1. Does this grouping make logical sense?
2. Are there any files that should be grouped differently?
3. Should any commits be split further or combined?
4. Are the commit messages clear and descriptive?

**Proceed with this plan? (Y/N)**
```

### Interactive Adjustments

Allow user to:

- **Reorder commits**: Adjust sequence if dependencies allow
- **Regroup files**: Move files between commits
- **Adjust messages**: Refine commit message wording
- **Split commits**: Break large commits into smaller ones
- **Combine commits**: Merge closely related commits

## Output Artifacts

### Store Analysis Results

**File**: `.ttt/memory/ttt-nice-git-commits/artifacts/commit-analysis.md`

```markdown
# Commit Analysis Results

## Original Commits (3)

### Commit 1: abc123def456

**Message**: WIP: authentication work
**Author**: John Doe
**Timestamp**: 2026-01-14T10:20:00Z
**Files Changed**: 15

**Categorized Files**:

- **Auth Core** (3): src/auth/jwt.js, src/auth/validator.js, src/auth/middleware.js
- **Configuration** (1): config/auth.config.js
- **Tests** (1): tests/auth/jwt.test.js
- **Documentation** (1): docs/api/auth.md
  ...
```

**File**: `.ttt/memory/ttt-nice-git-commits/artifacts/atomic-commit-plan.md`

Store the complete commit plan with all details (as shown in "Presenting Plan to User" section).

## Best Practices for AI Agents

### Analyze Thoroughly Before Planning

```javascript
// Don't rush to planning
1. Collect all commit data
2. Analyze file relationships
3. Detect dependencies
4. Consider build/test order
5. THEN plan atomic structure
```

### Respect Dependencies

```javascript
// Wrong: Tests before implementation
1. feat(auth): add JWT validation
2. test(auth): add JWT tests  // Depends on #1
3. feat(user): add user model
4. test(user): add user tests  // Depends on #3

// Correct: Implementation before tests
1. feat(auth): add JWT validation
2. feat(user): add user model
3. test(auth): add JWT tests     // After #1
4. test(user): add user tests     // After #2
```

### Keep Commits Atomic but Meaningful

```javascript
// Too granular (avoid)
1. feat(auth): add jwt.js
2. feat(auth): add validator.js
3. feat(auth): add middleware.js

// Appropriate (prefer)
1. feat(auth): add JWT token validation
   Files: jwt.js, validator.js, middleware.js
```

### Use Project Context

```javascript
// Read project configuration
const projectSetup = readFile(".ttt/config/project-setup.md");

// Extract preferences
const preferredScopes = extractScopesFromSetup(projectSetup);

// Apply to commit planning
const commits = planCommits(files, preferredScopes);
```

## Error Handling

### No Logical Grouping Found

If files have no clear relationships:

- Group by directory structure as fallback
- Keep commits smaller (2-3 files each)
- Use more generic commit messages
- Warn user about suboptimal grouping

### Circular Dependencies

If dependency cycle detected:

- Alert user immediately
- Suggest breaking cycle manually
- Provide options: skip dependency check or manual reordering
- Do not proceed automatically

### Too Many Small Commits

If plan results in >20 commits:

- Suggest combining related changes
- Ask user preference: detailed history vs conciseness
- Provide options to adjust granularity

## References

- **Main Skill**: [SKILL.md](SKILL.md)
- **State Management**: [state-management.md](state-management.md)
- **Atomic Commit Creation**: [atomic-commit-creation.md](atomic-commit-creation.md)
- **Conventional Commits Guide**: [resources/conventional-commits-guide.md](resources/conventional-commits-guide.md)
