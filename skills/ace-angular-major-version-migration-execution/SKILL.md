---
name: ace-angular-major-version-migration-execution
description: 'Execute one Angular major-version migration: branch, upgrade deps, apply guide steps, test, smoke-test, PR, and release.'
metadata:
  version: '1.3.0'
  authors:
  - name: Matthijs Vliegenthart
    email: matthijs.vliegenthart@partner.bmwgroup.com
  tags:
  - angular
  - migration
  - frontend
---

# Angular Major Version Migration Execution (per Application)

Run this skill once per application that was approved during the preparation phase. Use `<<story-key>>`, `<<version>>`, and `<<major>>` placeholders from the preparation output.

## Prerequisites

The following tools and environment variables must be available before starting the execution:

- **[jira-cli](../jira-cli/SKILL.md)** — Used throughout all steps to transition subtasks (In Progress / Close) and to read and update issue descriptions. Also requires `$JIRA_API_TOKEN` for REST API calls via `curl` (updating description content on unit test, component test, and dependency subtasks).
- **[gh-cli](../gh-cli/SKILL.md)** — Used in Step 7b to monitor the CI build, and in Step 10 and Step 12 to create, edit, and merge the pull request. Must be authenticated against `bmw.ghe.com` (use `GH_HOST=bmw.ghe.com gh auth status` to verify).
- **sonar CLI** (`sonar` at `~/.local/share/sonarqube-cli/bin/sonar`) — Used in Step 6 (SonarQube) to list issues for the migration branch. Must be authenticated against the correct SonarQube server (use `sonar auth status` to verify, and `sonar auth login --server <<sonar-server>> --with-token <<token>>` if needed). The server URL and project key are found in `sonar-project.properties`.
- **[ace-app-smoke-test](../ace-app-smoke-test/SKILL.md)** — Used in Step 10 to run a smoke test against the dev environment. Requires `python3`, `playwright` (`pip install playwright && playwright install chromium`), `Pillow` (`pip install Pillow`), and `kubectl` with `dev-k8s` / `acc-k8s` contexts.

## Step 1: Find JIRA Ticket and Put to "In Progress"

Ask the user which JIRA project key was used during preparation (e.g. `OEA`, `OPPS`) — store this as `$JIRA_PROJECT`.

Determine the current application name from the repository (e.g. from `package.json` or the root folder name). Then search for the corresponding JIRA story — it will have been created during the preparation phase with a title matching `"Migrate <<application>> to Angular Version <<version>>"`:

```bash
jira issue list -p $JIRA_PROJECT -tStory --plain --columns key,summary \
  | grep -i "<<application>>"
```

Identify the correct story by confirming both the **application name** and the **target Angular version** appear in the title. If multiple results are returned, ask the user to confirm which story key to use.

Once confirmed, transition the story to **In Progress**:

```bash
jira issue move <<story-key>> "In Progress"
```

### Load Subtask Keys

Fetch all subtasks of the story and extract each key by matching the summary. Store the results — you will use these throughout the remaining steps:

```bash
source references/load-subtask-keys.sh <<story-key>>
```

See [references/load-subtask-keys.sh](references/load-subtask-keys.sh) for the full script.

Verify all keys are populated before continuing. If any variable is empty, rerun the grep with a broader keyword.

## Step 2: Create Branch

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_CREATE_BRANCH "In Progress"
```

Detect the GitHub org/repo from the git remote and store it — this is used in all subsequent `gh` commands:

```bash
GH_REPO=$(git remote get-url origin | sed 's|.*[:/]\([^/]*/[^/]*\)\.git|\1|')
echo "Repository: $GH_REPO"
```

Detect the default branch name (it may be `master` or `main`):

```bash
git remote show origin | grep "HEAD branch" | awk '{print $NF}'
```

Create a new branch from the default branch and switch to it:

```bash
git checkout <<default-branch>>
git checkout -b chore/<<story-key>>-migrate-to-angular-<<version>>
```

> **Note:** Do not run `git pull` as it may prompt for credentials. The branch should already be up to date from the last fetch.

Mark the subtask **Done**:

```bash
jira issue move $SUB_CREATE_BRANCH "Close"
```

## Step 3: Upgrade Angular and Dependencies

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_UPDATE_ANGULAR "In Progress"
```

### Detect Project Type and Package Manager

Check whether the project is an Nx monorepo or a standalone Angular CLI project, and which package manager it uses:

```bash
# Nx monorepo: nx.json is present
ls nx.json 2>/dev/null && echo "Nx monorepo" || echo "Standalone Angular CLI"

# Package manager: check for lockfile
ls pnpm-lock.yaml 2>/dev/null && echo "pnpm" || (ls package-lock.json 2>/dev/null && echo "npm" || echo "unknown")
```

Use the detected package manager for **all** install and add commands throughout the remaining steps — replace `pnpm` with `npm` where applicable. For Nx commands, replace `pnpm exec nx` with `npx nx` when using npm.

Then follow **[references/upgrade-commands.md](references/upgrade-commands.md)** for:
1. Fix `nx.json` package manager (Nx monorepo only)
2. Run the migration (`nx migrate` or `ng update`)
3. Update Angular CLI and DevKit packages (Nx monorepo)
4. Update Angular ecosystem packages (`@angular/cdk`, `@angular/material`, etc.)
5. Update remaining dependencies from `$SUB_UPDATE_DEPS` subtask (move subtask **In Progress** → **Close** when done)
6. Install and resolve peer dependency warnings
7. Format migration changes with Prettier and fix compilation errors

Mark the **Update Angular** subtask **Done** after step 2; the **Update dependencies** subtask is managed within the reference guide.

## Step 4: Implement Angular Update Guide Steps

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_UPDATE_GUIDE "In Progress"
```

Read the subtask description to get the full list of steps, then **assess each step** before doing any work:

```bash
jira issue view $SUB_UPDATE_GUIDE --plain
```

For each step, search the codebase to determine its verdict:

| Verdict | Meaning | Action | Icon |
|---|---|---|---|
| **Do it** | Copilot found the pattern and made code changes | Implement immediately | `(/)` |
| **N/A / Already done** | Pattern not present, or already handled by a previous step | Note reason in Result column | `(?)` |
| **Deferred** | Could not act — only detectable at test runtime (timing, fakeAsync) | Note "Deferred - assess after running tests" in Result column | `(!)` |
| **Below threshold** | Copilot success % is below the agreed threshold | Note "Below threshold" in Result column | `(-)` |

For each **"Do it"** step:
1. Make the required code changes.
2. Adjust unit tests impacted by the change.
3. Adjust component tests impacted by the change.

After assessing and completing all applicable steps, update the subtask description via the Jira REST API with `(/)` / `( )` icons and a **Result** column:

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]
payload = json.dumps({"fields": {"description": "<<updated-description-with-results>>"}})
subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", payload,
    "https://atc.bmwgroup.net/jira/rest/api/2/issue/<<subtask-key>>"],
    capture_output=True, text=True)
```

Steps below the agreed Copilot success % threshold, or with a **Deferred** verdict, must be flagged to the user for manual handling after tests are run.

Mark the subtask **Done**:

```bash
jira issue move $SUB_UPDATE_GUIDE "Close"
```

## Step 5: Implement New Angular Version Features

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_NEW_FEATURES "In Progress"
```

Work through each **approved** feature from the "Implement New Angular Version features" subtask (populated during preparation).

Apply the same **assess → Do it / N/A / Deferred** verdict pattern as Step 4 for each feature. Update the subtask description with results using the same REST API pattern.

Mark the subtask **Done**:

```bash
jira issue move $SUB_NEW_FEATURES "Close"
```

## Step 6: Test the Code

Run the full test suite and verify the application is stable after all changes. Follow **[references/testing-guide.md](references/testing-guide.md)** for all commands and failure patterns, covering:

1. **Lint** — run against all affected Nx projects; fix errors, ignore pre-existing warnings
2. **Unit Tests** (`$SUB_UNIT_TESTS` In Progress → Close) — reset Nx cache, run targeted then full suite; see reference for common Angular 19 DI failures and how to distinguish resource-contention flakes from real regressions
3. **Component Tests** (`$SUB_COMPONENT_TESTS` In Progress → Close) — run via `nx run-many --target=component-test`; re-run individually to confirm any flakes
4. **Storybook** (if applicable) — verify `storybook:build` passes
5. **SonarQube** (`$SUB_SONARQUBE` In Progress → Close) — fetch issues for the branch, present MAJOR+ findings to the user, and ask whether to fix before proceeding

## Step 7: Commit the Code

Stage and commit all changes with a clear message:

```bash
git add .
git commit -m "(<<story-key>>): migrate to Angular <<version>>"
git push origin chore/<<story-key>>-migrate-to-angular-<<version>>
```

## Step 7b–12: Deliver and Release

Follow **[references/delivery-release.md](references/delivery-release.md)** for all remaining steps:

- **Step 7b** — Launch a background agent to monitor the CI build; fix any failures before continuing
- **Step 8** — Create the PR (title, body, labels, assignee), run the `code-review` agent, post findings as a PR comment, move story to **Review**
- **Step 9** — Ask user to trigger E2E via Slack (`#sit-support`), then launch a background agent to monitor; close subtask when all jobs pass
- **Step 10** — Run smoke test via `ace-app-smoke-test` skill; present results and wait for user confirmation before proceeding
- **Step 11** — Wait for human PR approval
- **Step 12** — Ask user to trigger release via Slack (`#merge-token`), monitor pipeline, validate on STG-1, then close all remaining subtasks and the story
```
