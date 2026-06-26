---
name: ace-angular-major-version-migration-preparation
description: 'Plan an Angular major-version migration: find target apps, assess effort, fetch update steps, and create Jira epics, stories, and subtasks.'
metadata:
  version: '1.2.0'
  authors:
  - name: Matthijs Vliegenthart
    email: matthijs.vliegenthart@partner.bmwgroup.com
  tags:
  - angular
  - migration
  - frontend
---

# Angular Major Version Migration Preparation

## Prerequisites

The following tools and skills must be available before starting the preparation:

- **[gh-cli](../gh-cli/SKILL.md)** — Used in Step 6 to fetch `package.json` from GitHub repositories via `gh api`.
- **[jira-cli](../jira-cli/SKILL.md)** — Used in Steps 2, 3, and 6 to create epics, stories, subtasks, and update issue descriptions. Also requires `$JIRA_API_TOKEN` for REST API calls (setting epic links, components, board assignment, and description updates via `curl`).
- **[ace-git-workflow](../ace-git-workflow/SKILL.md)** — Branch naming convention (`chore/<<story-key>>-migrate-to-angular-<<version>>`).
- **Playwright** (`pip install playwright --break-system-packages && python3 -m playwright install chromium`) — Used in Step 4 (if included) to render the `angular.dev/update-guide` SPA and in Step 5 (if included) to fetch new features from `angular.love`.

## Step 1: Determine the Target Angular Version

Ask the user two questions before proceeding:
1. Which major Angular version they want to migrate to (e.g., `19`)
2. Which JIRA project key to use (e.g., `OEA`, `OPPS`) — store this as `$JIRA_PROJECT`

Do not proceed until the user provides both.

Once provided, resolve the **exact target version** — the highest available minor and patch for that major — from npm:

```bash
npm view @angular/core versions --json \
  | python3 -c "
import sys, json
major = <<version>>
vs = [v for v in json.load(sys.stdin) if v.startswith(f'{major}.') and '-' not in v]
print(vs[-1])
"
```

Use this resolved version (e.g. `19.2.5`) as `<<version>>` in all subsequent steps. Inform the user: *"The latest stable Angular <<major>> release is <<version>>. I will target this version."*

Then verify the following:

1. **Wait for the x.1.x patch** — warn the user if the resolved version is x.0.x, as it may be unstable. Recommend waiting for x.1.x.
2. Check the minimum **Node.js version** required for the target Angular version and verify the project is compatible.

### Check oasis-fe-mono is Already Migrated

If the application being migrated is **not** `oasis-fe-mono`, verify that `oasis-fe-mono` is already on the target Angular version before proceeding. `oasis-fe-mono` must always be migrated first, as other applications depend on it.

Fetch its current Angular version from GitHub:

```bash
gh api repos/OASIS/oasis-fe-mono/contents/package.json --jq '.content' \
  | base64 -d \
  | python3 -c "import sys,json; p=json.load(sys.stdin); print(p['dependencies'].get('@angular/core', p.get('devDependencies',{}).get('@angular/core','NOT FOUND')))"
```

If `oasis-fe-mono` is **not yet on the target version**, stop and inform the user:

> "⚠️ `oasis-fe-mono` is currently on Angular <<current-version>> and must be migrated to Angular <<version>> first. Please run this preparation skill for `oasis-fe-mono` before migrating other applications."

**Do not proceed until `oasis-fe-mono` is confirmed to be on the target version**, or until the user confirms they are currently preparing the `oasis-fe-mono` migration itself.

### Identify Applications to Migrate

Read [front-end-applications.md](references/front-end-applications.md) and identify which applications are **not yet on the target Angular version**. Exclude any application whose Angular version already matches the target.

For each application that requires migration, assess a **Migration Difficulty** percentage based on the following criteria:

- **Version gap** — each major version to cross adds complexity. One major version behind = low base difficulty; two or more = progressively higher.
- **Project type** — Nx monorepos are harder to migrate than standalone Angular CLI projects due to workspace-level coordination and additional Nx compatibility constraints.
- **Known outliers** — applications on significantly older versions (e.g., two or more majors behind) should be flagged with higher difficulty.

Use this scale as a guideline:

| Situation | Difficulty |
|-----------|-----------|
| 1 major version behind, Angular CLI | 20–35% |
| 1 major version behind, Nx monorepo | 35–50% |
| 2 major versions behind, Angular CLI | 50–65% |
| 2 major versions behind, Nx monorepo | 65–80% |
| 3+ major versions behind, any type | 75–95% |

Present the result to the user as a table. Add a **Recommendation** column based on the difficulty threshold:
- **✅ Include** — Migration Difficulty ≤ 40%
- **⚠️ Review manually** — Migration Difficulty > 40%

| # | Repository | Project Type | Current Version | Target Version | Migration Difficulty | Recommendation |
|---|-----------|-------------|-----------------|----------------|----------------------|----------------|
| 1 | ... | ... | ... | ... | XX% | ✅ Include / ⚠️ Review manually |

Then ask the user to approve the list:

> "These are the applications I identified for migration to Angular <<version>>. Please review the list and migration difficulty estimates. Confirm if you'd like to proceed with all of them, or let me know which ones to include or exclude."

**Do not proceed to Step 2 until the user explicitly approves the list.** If the user removes applications, carry forward only the approved subset for all subsequent steps.

## Step 2: Create a JIRA Epic

Create an Epic in the `$JIRA_PROJECT` project to track the migration:

```bash
jira issue create -tEpic -s"Migrate to Angular <<major>>" --no-input
```

Note the Epic key returned — it will be used when creating stories in later steps.

Then set the epic description to a table of all approved applications with their current and target versions, using the REST API:

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"description": "||Application||Current Version||Target Version||\n|<<app>>|<<current>>|<<version>>|\n..."}}' \
  "https://atc.bmwgroup.net/jira/rest/api/2/issue/<<epic-key>>"
```

Use a Python subprocess to build and POST the full description safely (avoids shell escaping issues with multi-line JSON).

## Step 3: Create JIRA Stories for Approved Angular Applications

First, retrieve the current unreleased fix version from the `$JIRA_PROJECT` project:

```bash
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://atc.bmwgroup.net/jira/rest/api/2/project/$JIRA_PROJECT/versions" \
  | python3 -c "
import sys, json
versions = json.load(sys.stdin)
unreleased = [v for v in versions if not v.get('released') and not v.get('archived')]
print(unreleased[-1]['name'] if unreleased else 'No unreleased version found')
"
```

Use the version returned as `<<fix-version>>`. If multiple unreleased versions are returned, confirm with the user which one to use.

For each application **approved by the user in Step 1**, create a story:

```bash
jira issue create -tStory \
  -s"Migrate <<application>> to Angular Version <<version>>" \
  -lFE-improvement \
  -lFeatureToggled-no \
  -lMarketTestingRequired-no \
  --priority High \
  --fix-version "<<fix-version>>" \
  --no-input
```

Then link the story to the Epic and set the component using the REST API (`--custom epic-link` does not work reliably):

Before setting the component, resolve its ID from the project:

```bash
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  "https://atc.bmwgroup.net/jira/rest/api/2/project/$JIRA_PROJECT/components" \
  | python3 -c "
import sys, json
comps = json.load(sys.stdin)
name = '<<component-name>>'
match = next((c for c in comps if c['name'].lower() == name.lower()), None)
print(match['id'] if match else 'NOT FOUND')
"
```

The component name is the human-readable name of the application (e.g. `Customer Agreement App` for `customer-agreement-app`). For Nx monorepos, look up the apps inside the monorepo (via `gh api repos/OASIS/<<application>>/contents/apps`) and add all matching components.

```bash
curl -s -X PUT \
  -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"fields": {"customfield_10001": "<<epic-key>>", "components": [{"id": "<<component-id>>"}]}}' \
  "https://atc.bmwgroup.net/jira/rest/api/2/issue/<<story-key>>"
```

Then add the story to the Kanban board (rapidView=78689):

```bash
curl -s -X POST \
  -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"issues": ["<<story-key>>"]}' \
  "https://atc.bmwgroup.net/jira/rest/agile/1.0/board/78689/backlog"
```

After creating each story, create the following subtasks under it:

```bash
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Create branch" -b"Branch name: chore/<<story-key>>-migrate-to-angular-<<version>>" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Update Angular Version to <<version>>" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Update dependencies" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Run unit tests" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Run component tests" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Check SonarQube" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Create PR" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Run E2E tests" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Manual test by the user" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Release" -P <<story-key>> --no-input
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Deploy to STG-1 & verify functionality and migrations" -P <<story-key>> --no-input
```

**Optional subtasks** — only create these if the user opted in during the corresponding step:

```bash
# Only if user chose to include Angular Update Guide steps (Step 4):
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Implement Angular Update Guide steps" -P <<story-key>> --no-input

# Only if user chose to include New Angular Features (Step 5):
jira issue create -p $JIRA_PROJECT -t"Sub-task" -s"Implement New Angular Version features" -P <<story-key>> --no-input
```

> ⚠️ The `-p $JIRA_PROJECT` flag is required. Without it, jira-cli defaults to its configured project, causing a "Sub-tasks must be created in the same project as the parent" error.

Repeat for all applications approved in Step 1.

## Step 4: Review Angular Update Guide Steps (Optional)

> **Ask the user:** *"Would you like to review and include the Angular Update Guide steps in this migration? This involves fetching the official update guide from angular.dev and assessing each step for Copilot automation. If skipped, the migration will only cover dependency updates (and optionally new features)."*
>
> If the user declines, skip this entire step and proceed to Step 5.

Determine the current Angular version by looking at the most common version in [front-end-applications.md](references/front-end-applications.md).

Fetch update guide steps using the Playwright script in **[references/update-guide-steps.md](references/update-guide-steps.md)** at Advanced complexity (`l=3`), which shows all steps regardless of difficulty level.

For each step in the guide, present it to the user in a table with a risk assessment and a success probability:

| # | Step | Level | Risk | Copilot Success Probability |
|---|------|-------|------|-----------------------------|
| 1 | ... | Basic / Medium / Advanced | High / Medium / Low | 0–100% |

Assess risk as follows:
- **High** — breaking changes, manual code rewrites, or runtime behavior impact
- **Medium** — configuration or tooling changes with moderate impact
- **Low** — straightforward automated changes (e.g., `ng update` handles it)

The **Copilot Success Probability** reflects how likely Copilot is to implement the step correctly: 90–100% for low-risk automated steps, 60–89% for medium-complexity changes, below 60% for high-risk or context-dependent steps.

Pre-suggest approving all steps with **Copilot Success Probability ≥ 80%**:

> "Based on the success probabilities, I suggest Copilot handles steps X, Y, Z (all with ≥ 80%). The remaining steps would be marked as manual. Do you approve this selection, or would you like to add or remove any steps?"

**Wait for the user's confirmation before proceeding.**

Once approved, update the "Implement Angular Update Guide steps" subtask on every story created in Step 3 with the **full table of all steps** as the description. See [references/update-guide-steps.md](references/update-guide-steps.md) for the REST API update pattern and Jira wiki markup format.

## Step 5: Review New Angular Features (Optional)

> **Ask the user:** *"Would you like to include new Angular features in this migration? This involves fetching and reviewing new features introduced in the target Angular version(s) from angular.love. If skipped, the migration will only cover the update guide steps and dependency updates."*
>
> If the user declines, skip this entire step and proceed to Step 6.

If migrating more than one major version (e.g. from v17 to v19), fetch features for **each intermediate and target version** (e.g. v18 and v19) and combine into a single table grouped by version.

Fetch new features using the Playwright script in **[references/new-features.md](references/new-features.md)**. Only use `https://angular.love/angular-<<major>>-whats-new` as the source.

For each feature, present it to the user in a combined table grouped by version:

| # | Version | Feature | Risk | Copilot Success Probability |
|---|---------|---------|------|-----------------------------|
| 1 | Angular X | ... | High / Medium / Low | 0–100% |

Apply the same risk and probability criteria as Step 4.

Pre-suggest implementing all features with **Copilot Success Probability ≥ 80%**:

> "Based on the success probabilities, I suggest Copilot implements features X, Y, Z (all with ≥ 80%). The remaining features would be marked as manual. Do you approve this selection, or would you like to add or remove any features?"

**Wait for the user's confirmation before proceeding.**

Once approved, update the "Implement New Angular Version features" subtask on every story created in Step 3 with the **full table of all features** as the description. See [references/new-features.md](references/new-features.md) for the REST API update pattern and Jira wiki markup format.

## Step 6: Analyze Dependencies to Update

Identify which dependencies need to be updated alongside Angular for the target version. Follow **[references/dependency-analysis.md](references/dependency-analysis.md)** for all commands, covering:

1. Fetch each application's `package.json` from GitHub via `gh api`
2. Resolve the `oasis-fe-mono` dependency version (if applicable)
3. Resolve exact target versions from npm for all Angular-related and peer dependencies
4. Build the dependency table (flag ambiguous packages with ⚠️)
5. Update the **"Update Angular Version"** subtask with Angular packages (`@angular/`, `@angular-devkit/`, `@schematics/angular`)
6. Update the **"Update dependencies"** subtask with all other packages

Repeat for all stories created in Step 3.
