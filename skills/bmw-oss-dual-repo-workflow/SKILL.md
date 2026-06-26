---
name: bmw-oss-dual-repo-workflow
description: Manage BMW internal mirror review and public GitHub publication for open-source contributions that require an internal PR before a public PR.
license: Proprietary
compatibility: Requires git and gh CLI. Creating internal PRs also requires authenticated gh access to cc-github.bmwgroup.net.
metadata:
  authors:
    - Simon Duerr <simon.duerr@bmw.de>
  version: "1.0.0"
  tags:
    - bmw
    - git
    - github
    - open-source
    - pull-request
    - workflow
    - internal-review
---

# bmw-oss-dual-repo-workflow

## Goal

Handle the BMW dual-repository contribution flow for open-source changes: create the internal review PR against the BMW mirror first, keep that PR review-only, and create the public PR only after internal review is complete.

## When to use

- User needs an internal review PR against the BMW mirror in the `oss` organization on `cc-github.bmwgroup.net`
- User needs to push the same branch to internal and public forks
- User needs help choosing the correct PR template for the internal mirror versus the public repository
- User needs a public PR prepared after internal review is complete
- User needs to manage an internal review-only PR that must not be merged

## When not to use

- The change is fully internal and has no public open-source repository to publish to
- The user wants to skip internal review and publish directly to the public repository
- The task is only normal single-repository PR creation with no internal mirror involved

## Inputs

- Current branch name
- Internal fork remote name
- Internal mirror repository under `oss/<repository>`
- Public fork remote name
- Public upstream repository
- Default branch for the internal mirror and public upstream
- Whether internal review is complete
- Local validation results for the change

## Outputs

- Internal PR URL when internal review is requested
- Public PR URL when public publication is requested and allowed
- Short validation summary describing what was run and any local validation gaps
- Explicit note that the internal PR is review-only and must not be merged

## Guardrails

1. Internal review is required before public publication.
2. Internal PRs exist only for internal review and are not merged.
3. Public GitHub workflows do not run on the internal PRs, so internal PR status is not the publication gate.
4. Internal mirrors of BMW-contributed open-source projects are hosted under the `oss` organization on `cc-github.bmwgroup.net`.
5. Never copy confidential BMW-only details, internal tickets, internal hostnames, internal paths, private review notes, or personal data into the public PR.
6. Always verify remote names, repository owners, repository names, and default branches before pushing or creating PRs.
7. Always use the effective PR template of the target repository. Do not assume the internal and public templates match.
8. If the user asks to skip internal review and open the public PR first, refuse that sequence and offer to create or update the internal PR first.

## Repository roles

- Public upstream repository: the canonical public open-source repository
- Public fork remote: the remote that points to the contributor's public fork
- Internal upstream repository: the BMW internal mirror hosted as `oss/<project-repository>` on `cc-github.bmwgroup.net`
- Internal fork remote: the remote that points to the contributor's internal fork of that internal mirror

Do not hard-code remote names such as `origin` or `upstream` without checking. Always inspect the actual remotes first.

## Validation

"Relevant local validation" means the strongest local checks that best predict whether the change will pass the public repository's review and CI gates.

Choose validation in this order:

1. Inspect the public repository's CI workflows, required checks, or normal PR checks.
2. Inspect repository documentation and tooling to find supported local equivalents such as `README`, `CONTRIBUTING`, workspace tasks, package scripts, `pytest`, `cargo test`, `gradle test`, `ctest`, lint, format, type-check, and static-analysis commands.
3. Start with the changed area first:
   - build the touched target or package
   - run the affected tests
   - run the linters, formatters, type checks, or static analysis used for the touched files
4. Broaden the scope when the change is cross-cutting, affects shared build or CI configuration, changes public APIs, or when public CI always runs a wider required suite.
5. If the exact public CI checks cannot be run locally, run the closest supported subset and state the limitation clearly in the PR.

Examples:

- C or C++: build affected targets, run relevant tests, run configured formatting or static analysis used by CI
- Python: run affected tests plus lint and type checks used by CI
- Rust: run affected tests plus `cargo check`, `cargo clippy`, and format checks if the project uses them
- JavaScript or TypeScript: run affected tests, build, lint, and type-check commands enforced by CI

Always summarize:

- what was run
- why those checks were chosen
- what could not be validated locally

## Workflow

### 1. Prepare the branch

1. Confirm the current branch with `git branch --show-current`.
2. Check for unrelated local changes with `git status --short` and avoid disturbing them.
3. Inspect remotes and identify the internal fork, public fork, internal mirror, and public upstream with `git remote -v`.
4. Determine and run the relevant local validation, because the internal PR does not replace public CI.
5. Keep the same branch name across internal and public forks when practical.

### 2. Create the internal review PR

1. Push the branch to the internal fork remote.
2. Create a cross-repository PR from the internal fork branch to the internal mirror repository's default branch in the `oss` organization.
3. Use `GH_HOST=cc-github.bmwgroup.net` for internal GitHub CLI commands.
4. Before writing the PR body, verify the effective internal template by checking the target repository's template files, API, or a recent internal PR.
5. Fill the internal template completely.
6. Include:
   - what changed
   - how the change was validated locally
   - that the PR is for internal review only
   - that the PR must not be merged
   - an internal ticket or tracking reference only if the user explicitly wants it
7. Do not state or imply that the internal PR will be merged.
8. Share the internal PR URL with the user.

### 3. Create the public PR

Only do this after internal review is complete.

1. Push the same change to the public fork remote.
2. Open the public PR from the public fork branch to the public upstream repository's default branch.
3. Verify and use the public repository's PR template.
4. Remove internal-only details, including:
   - internal ticket numbers unless explicitly safe for public use
   - BMW-only process notes
   - confidential paths, hosts, people, or review commentary
5. Write the public PR description for an external open-source audience.
6. Share the public PR URL with the user.

### 4. After publication

1. Do not merge the internal PR.
2. Leave the internal PR open unless the user explicitly asks to close it or the project's internal process requires closure.
3. Update Jira or other internal tracking systems only when the user explicitly requests it.

## PR guidance

### Internal PR

Focus on internal review and compliance.

Include:

- a concise summary of the change
- the local validation that was run
- why those validation steps were the relevant checks for the change
- an explicit statement that the PR is for internal review only and must not be merged

### Public PR

Focus on the code change, tests, and public context.

Include:

- what changed
- why it changed
- public-facing validation or test results
- public issue references only when requested or already part of the public workflow

Do not include internal review mechanics in the public PR description.

## Related skills

- <skill>pr-creation</skill>: Use for stronger PR body generation, template handling, reviewer assignment, and ticket alignment once this skill has determined which PR should be created and when.
- <skill>resolve-pr-comments</skill>: Use after the internal or public PR receives review feedback that requires code changes or thread resolution.
- <skill>pr-overview</skill>: Use to inspect PR status, review state, and CI progress when deciding whether internal review is complete or whether the public PR is healthy.
- <skill>git-commit-reorganization</skill>: Use before creating either PR when the branch history is too messy for effective internal or public review.
- <skill>fix-gh-build-error</skill>: Use after the public PR is opened if GitHub Actions fail and the user wants the failing workflow diagnosed and fixed.

## Command patterns

```bash
git remote -v
git branch --show-current

git push -u <internal-fork-remote> HEAD
GH_HOST=cc-github.bmwgroup.net gh pr create \
  --repo oss/<internal-mirror-repository> \
  --base <internal-default-branch> \
  --head "<internal-fork-owner>:<branch>"

git push -u <public-fork-remote> HEAD
gh pr create \
  --repo <public-upstream-owner>/<public-upstream-repository> \
  --base <public-default-branch> \
  --head "<public-fork-owner>:<branch>"
```

## Completion checklist

- [ ] Branch pushed to the intended fork or forks
- [ ] Relevant local validation completed
- [ ] Validation summary prepared
- [ ] Internal PR created against the internal mirror repository in the `oss` organization
- [ ] Internal PR body uses the effective internal template
- [ ] Internal PR clearly marked as review-only and not for merge
- [ ] Public PR created only when requested and only after internal review is complete
- [ ] Public PR uses the public repository template
- [ ] Public PR omits internal-only information
