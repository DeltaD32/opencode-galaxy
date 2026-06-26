# Testing Guide Reference

Detailed commands for Step 6 of the Angular major version migration.

## Lint

Run lint across all projects affected by the migration. Identify the Nx project names from the changed file paths:

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx run-many --target=lint \
  --projects=<<comma-separated-project-names>> --skip-nx-cache > /tmp/lint-output.txt 2>&1

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx run-many --target=lint \
  --projects=<<comma-separated-project-names>> --skip-nx-cache > /tmp/lint-output.txt 2>&1

echo "EXIT CODE: $?"
tail -5 /tmp/lint-output.txt
```

A non-zero exit code means lint errors must be fixed before continuing. Warnings (e.g. `@angular-eslint/prefer-standalone`, `@typescript-eslint/no-explicit-any`) are expected and pre-existing — do not fix them unless they are new errors introduced by your changes.

## Unit Tests

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_UNIT_TESTS "In Progress"
```

Reset the Nx cache before running, to avoid stale "failed" results from the pre-migration test run:

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx reset

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx reset
```

Run tests for the primary application project first (faster, surfaces real failures):

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx test <<app-project-name>> --no-coverage --skip-nx-cache

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx test <<app-project-name>> --no-coverage --skip-nx-cache
```

Once the targeted run is clean, run the full suite:

```bash
# pnpm
pnpm test

# npm
npm test
```

### Common Angular 19 Test Failures

Angular 19 makes dependency injection stricter. Tests that passed under Angular 18 may fail with `NullInjectorError` for providers that were previously resolved automatically.

**Pipes used via `inject()`**: If a standalone pipe (e.g. `AlCurrencyPipe`) calls `inject(CurrencyPipe)` internally, `CurrencyPipe` must be explicitly added to `providers` in `TestBed`:

```typescript
TestBed.configureTestingModule({
  providers: [
    CurrencyPipe, // add when inject(CurrencyPipe) throws NullInjectorError
    ...
  ]
});
```

**Child components with deep DI chains**: If a non-mocked child component depends on a service (e.g. NGXS `Store`, `AlTenantService`) with transitive dependencies (e.g. `OAuthService`), provide a mock for that service rather than mocking the child component:

```typescript
TestBed.configureTestingModule({
  providers: [
    provideNgxs(),                                           // satisfies Store → CUSTOM_NGXS_EXECUTION_STRATEGY chain
    {provide: AlTenantService, useValue: tenantServiceMock}, // satisfies AlTenantService → OAuthService chain
    ...
  ]
});
```

### Interpreting Full-Suite Failures

When `pnpm test` / `npm test` reports "Failed tasks" for many projects, verify those projects individually:

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx test <<project-name>> --no-coverage --skip-nx-cache

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx test <<project-name>> --no-coverage --skip-nx-cache
```

If a project passes individually but appears in "Failed tasks" from the full run, the failure is due to **system resource contention** (parallel Jest workers competing for CPU/memory), not a migration regression. Document this in the JIRA subtask and proceed.

### Update Subtask via Jira REST API

After all failures are resolved, update the subtask description:

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]

description = """h2. Unit Test Results

*Total: <<N>> passed, <<S>> skipped — <<app-project-name>>*

h3. Failing Suites Fixed

||Suite||Root Cause||Fix||
|<<suite-file>>|<<root-cause>>|<<fix-applied>>|

h3. Full Suite Observation

<<Either: "All projects passed in the full test run."
  Or:     "Running pnpm test / npm test (all N projects, parallel=8) lists X projects under Failed tasks.
           Each passes individually with --skip-nx-cache. These failures are caused by system
           resource contention and are pre-existing — not introduced by this migration.">>"""

payload = json.dumps({"fields": {"description": description}})
subprocess.run(
    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT",
     "-H", f"Authorization: Bearer {token}",
     "-H", "Content-Type: application/json",
     "-d", payload,
     "https://atc.bmwgroup.net/jira/rest/api/2/issue/<<SUB_UNIT_TESTS>>"],
    capture_output=True, text=True
)
```

Mark the subtask **Done**:

```bash
jira issue move $SUB_UNIT_TESTS "Close"
```

## Component Tests

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_COMPONENT_TESTS "In Progress"
```

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx run-many --target=component-test --all --browser=chrome

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx run-many --target=component-test --all --browser=chrome
```

If a project appears in "Failed tasks" but passes individually, re-run the full suite once to rule out a flake. Component tests can occasionally fail in parallel due to browser resource constraints:

```bash
# pnpm
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx component-test <<project-name>> --browser=chrome

# npm
NX_SKIP_PROVENANCE_CHECK=true npx nx component-test <<project-name>> --browser=chrome
```

After the run is clean, update the subtask description via the Jira REST API:

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]

description = """h2. Component Test Results

*Total: <<N>> projects passed — all specs green*

h3. Suite Summary

||Result||Projects||Specs||
|(/) All passed|<<N>>|<<total-specs>>|

h3. Full Suite Observation

<<Either: "All N projects passed in the full nx run-many component-test run."
  Or:     "Project(s) <<names>> appeared in Failed tasks on the first run but passed individually
           and on re-run — confirmed as browser resource flakes, not migration regressions.">>"""

payload = json.dumps({"fields": {"description": description}})
subprocess.run(
    ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT",
     "-H", f"Authorization: Bearer {token}",
     "-H", "Content-Type: application/json",
     "-d", payload,
     "https://atc.bmwgroup.net/jira/rest/api/2/issue/<<SUB_COMPONENT_TESTS>>"],
    capture_output=True, text=True
)
```

Mark the subtask **Done**:

```bash
jira issue move $SUB_COMPONENT_TESTS "Close"
```

## Storybook (if applicable)

If the project includes Storybook, verify it builds and renders without errors:

```bash
# pnpm
pnpm run storybook:build

# npm
npm run storybook:build
```

## SonarQube

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_SONARQUBE "In Progress"
```

Ensure you are logged in (`sonar auth status`; use `sonar auth login` if needed). Read the project key from `sonar-project.properties`:

```bash
sonar list issues \
  --project <<sonar.projectKey>> \
  --branch <<current-branch>> \
  --format json | python3 -c "
import json, sys
data = json.load(sys.stdin)
issues = data.get('issues', [])
total = data.get('total', 0)

from collections import Counter
types = Counter(i.get('type') for i in issues)
severities = Counter(i.get('severity') for i in issues)

import datetime
current_year = str(datetime.datetime.now().year)
new_issues = [i for i in issues if i.get('creationDate','').startswith(current_year)]

print(f'Total issues: {total}')
print('By type:', dict(types))
print('By severity:', dict(severities))
print(f'New issues ({current_year}): {len(new_issues)}')

major_new = [i for i in new_issues if i.get('severity') in ('BLOCKER', 'CRITICAL', 'MAJOR')]
if major_new:
    print()
    print('MAJOR+ new issues:')
    for i in major_new:
        print(f'  [{i.get(\"severity\")}] {i.get(\"message\",\"\")[:100]}')
        print(f'    File: {i.get(\"component\",\"\").split(\":\")[-1]}')
"
```

Present the summary to the user in a clear table:

| Severity | Type | Count |
|----------|------|-------|
| 🔴 MAJOR+ | ... | N |
| 🟡 MINOR | ... | N |
| ⚪ INFO | ... | N |

Highlight any **BLOCKER**, **CRITICAL**, or **MAJOR** issues with their file and message. INFO/MINOR issues in `.cy.ts` test files are typically pre-existing code smells unrelated to the migration.

Ask the user whether they want to:
1. Fix the MAJOR+ issues before continuing
2. Proceed without fixing them

Only mark the subtask **Done** once the user confirms:

```bash
jira issue move $SUB_SONARQUBE "Close"
```
