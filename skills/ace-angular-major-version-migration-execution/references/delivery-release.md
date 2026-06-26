# Delivery & Release Reference

Detailed instructions for Steps 7b–12 of the Angular major version migration.

## Step 7b: Monitor CI Build

After pushing, a CI pipeline is triggered automatically. Launch a background agent to monitor it:

```
Launch a background agent with the following prompt:

  Monitor the GitHub Actions CI build that was just triggered on repository $GH_REPO
  at host bmw.ghe.com for branch chore/<<story-key>>-migrate-to-angular-<<version>>.

  First, find the run ID:
    GH_HOST=bmw.ghe.com gh run list --repo $GH_REPO \
      --branch chore/<<story-key>>-migrate-to-angular-<<version>> --limit 1

  Then watch it to completion:
    GH_HOST=bmw.ghe.com gh run watch <<run-id>> --repo $GH_REPO

  Once complete, report:
  1. Final status of each job (✅ pass / ❌ fail)
  2. If any job failed, fetch logs:
       GH_HOST=bmw.ghe.com gh run view <<run-id>> --repo $GH_REPO --log-failed
     and report the key error lines
  3. Overall summary: PASS ✅ or FAIL ❌

  This pipeline may take 20-30 minutes — wait for full completion before reporting.
```

You will be notified automatically when the agent completes. If any job fails, investigate and fix the errors before proceeding to Step 8.

## Step 8: Create Pull Request

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_CREATE_PR "In Progress"
```

Create a PR using the `gh-cli` skill. The PR body in [pr-body.md](pr-body.md) is based on the repository's `.github/pull_request_template.md` with the migration details pre-filled. Fill in the placeholders before creating:

```bash
gh pr create \
  --title "chore(<<story-key>>): migrate to Angular <<version>>" \
  --body "$(cat references/pr-body.md)" \
  --label "major release" \
  --label "angular-<<major>>"
```

Then assign the PR to the user who created it:

```bash
gh pr edit <<pr-number>> --add-assignee <<github-username>>
```

After the PR is created, share the PR URL with the user:

> "PR created: <<pr-url>>. I've put the story to Review."

Add the PR link to the subtask description:

```bash
jira issue edit $SUB_CREATE_PR --no-input -b"PR: <<pr-url>>"
```

### Copilot Code Review

Perform an automated code review on the PR using the `code-review` agent. Focus on:

- Deprecated APIs removed in Angular `<<major>>`
- Incorrect or mismatched version bumps across `@angular/*` packages
- Partially applied migrations (e.g. mixed old/new syntax in the same file)
- Angular best practice violations introduced by this PR (signals, standalone components, native control flow, no `ngClass`/`ngStyle`, `inject()` over constructor injection)
- Bugs or logic errors introduced by the migration changes

Only flag issues that genuinely matter — do **not** comment on pre-existing code untouched by this PR, formatting, or style preferences.

Once the review is complete, post the findings as a comment on the PR:

```bash
GH_HOST=bmw.ghe.com gh pr comment <<pr-number>> \
  --repo $GH_REPO \
  --body "<<review-findings>>"
```

If no issues are found, post a brief approval comment confirming the migration looks clean.

Mark the subtask **Done** and transition the story to **Review**:

```bash
jira issue move $SUB_CREATE_PR "Close"
jira issue move <<story-key>> "Review"
```

## Step 9: Run E2E Tests

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_E2E_TESTS "In Progress"
```

### 9a. Trigger via Slack

E2E tests cannot be triggered automatically — they must be requested via Slack. Ask the user to do the following:

> "Please trigger the E2E test suite by posting the following command in the **#sit-support** Slack channel:
>
> `/claim <<story-key>>`
>
> Let me know once it has been started so I can begin monitoring the jobs."

**Wait until the user confirms the E2E run has been started before continuing.**

### 9b. Monitor E2E Jobs

Once the user confirms the run has started, launch a background agent to monitor it:

```
Launch a background agent with the following prompt:

  Monitor the GitHub Actions E2E test run that was just triggered on repository $GH_REPO
  at host bmw.ghe.com for branch chore/<<story-key>>-migrate-to-angular-<<version>>.

  First, find the most recent run for this branch that contains an e2e job:
    GH_HOST=bmw.ghe.com gh run list --repo $GH_REPO \
      --branch chore/<<story-key>>-migrate-to-angular-<<version>> --limit 5

  Identify the run ID of the E2E workflow run (look for workflow names containing "e2e" or "cypress"),
  then watch it to completion:
    GH_HOST=bmw.ghe.com gh run watch <<run-id>> --repo $GH_REPO

  Once complete, report:
  1. Final status of each job (✅ pass / ❌ fail)
  2. If any job failed, fetch logs:
       GH_HOST=bmw.ghe.com gh run view <<run-id>> --repo $GH_REPO --log-failed
     and report the key error lines
  3. Overall summary: PASS ✅ or FAIL ❌

  E2E pipelines may take 20-40 minutes — wait for full completion before reporting.
```

You will be notified automatically when the agent completes. If any job fails, investigate and fix the errors before proceeding. Once all jobs pass, mark the subtask **Done**:

```bash
jira issue move $SUB_E2E_TESTS "Close"
```

## Step 10: Regression Test

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_MANUAL_TEST "In Progress"
```

Run a smoke test using the `ace-app-smoke-test` skill to automatically compare the migrated app on dev against the staging baseline.

### 10a. Discover Routes

Invoke the **`ace-app-navigator`** skill on the current repository to produce a navigation map for `<<application>>`. From the resulting guide:

- Collect all **testable routes** (absolute URL paths, e.g. `/my-app/overview`)
- **Skip** any route that contains a URL parameter (`:paramName` segment)
- Build a comma-separated `ROUTES` list, e.g.:

```bash
ROUTES="/lease-contract-sales/tasks,/lease-contract-sales/campaign,/lease-contract-sales/contract"
```

### 10b. Ask for Dev Server

Ask the user:

> "Which dev environment number should I run the regression test on? (e.g. 10 for dev-10)"

Store the answer as `DEV_SERVER`.

### 10c. Run the Regression Test

```bash
python3 <<path-to-skill>>/ace-app-smoke-test/scripts/regression_test.py \
  --server $DEV_SERVER \
  --username ace_superuser_<<tenant>> \
  --password test \
  --app <<application>> \
  --routes "$ROUTES"
```

Where `<<tenant>>` is the lowercase tenant code for the dev environment (auto-detected by the script from the env repo, or ask the user if unknown). The `<<path-to-skill>>` is the resolved path to the `ace-app-smoke-test` skill directory (typically `~/.copilot/skills/ace-app-smoke-test` or the local toolkit path).

### 10d. Present Results and Ask to Continue

Show the full regression summary output to the user. Then ask:

> "The regression test completed: **X/Y routes passed**.
>
> | Route | Status |
> |-------|--------|
> | ... | ... |
>
> Routes marked `✅ PASS (ℹ️ empty state on dev)` passed with data-sensitive metrics skipped — this is expected when dev has no data.
>
> Do you want to proceed to creating the PR, or would you like to investigate a regression first?"

**Do not proceed to Step 11 until the user explicitly confirms.**

Once confirmed, mark the subtask **Done**:

```bash
jira issue move $SUB_MANUAL_TEST "Close"
```

## Step 11: Human PR Approval

Wait for a human reviewer to approve the PR. Do not merge until at least one approval is received.

## Step 12: Release

Move the subtask to **In Progress**:

```bash
jira issue move $SUB_RELEASE "In Progress"
```

### 12a. Trigger via Slack

The release cannot be triggered automatically — it must be requested via Slack. Ask the user to do the following:

> "Please trigger the release by posting the following command in the **#merge-token** Slack channel:
>
> `/release <<story-key>>`
>
> Let me know once it has been started so I can begin monitoring the pipeline."

**Wait until the user confirms the release has been started before continuing.**

### 12b. Monitor Release Pipeline

Once the user confirms the release has started, launch a background agent to monitor it:

```
Launch a background agent with the following prompt:

  Monitor the GitHub Actions release pipeline that was just triggered on repository $GH_REPO
  at host bmw.ghe.com for branch chore/<<story-key>>-migrate-to-angular-<<version>>.

  First, find the most recent release workflow run:
    GH_HOST=bmw.ghe.com gh run list --repo $GH_REPO \
      --branch chore/<<story-key>>-migrate-to-angular-<<version>> --limit 5

  Identify the run ID of the release workflow run (look for workflow names containing "release" or "deploy"),
  then watch it to completion:
    GH_HOST=bmw.ghe.com gh run watch <<run-id>> --repo $GH_REPO

  Once complete, report:
  1. Final status of each job (✅ pass / ❌ fail)
  2. If any job failed, fetch logs:
       GH_HOST=bmw.ghe.com gh run view <<run-id>> --repo $GH_REPO --log-failed
     and report the key error lines
  3. Overall summary: PASS ✅ or FAIL ❌

  Release pipelines may take 10-20 minutes — wait for full completion before reporting.
```

You will be notified automatically when the agent completes. If any job fails, investigate and report to the user before continuing.

### 12c. Validate on STG

Once the release pipeline has succeeded, move the **Deploy to STG** subtask to **In Progress**:

```bash
jira issue move $SUB_RELEASE "Close"
jira issue move $SUB_DEPLOY_STG "In Progress"
```

Verify that the release has been deployed correctly to the STG-1 environment and that the application is functioning as expected.

### 12d. Close Out

Once validated, mark the deploy subtask **Done**, transition the story to **Done**, and clean up the local branch:

```bash
jira issue move $SUB_DEPLOY_STG "Close"
jira issue move <<story-key>> "Close"
git checkout <<default-branch>>
git branch -d chore/<<story-key>>-migrate-to-angular-<<version>>
```
