# Dependency Analysis Reference

Detailed commands for Step 6 of the Angular major version migration preparation.

## Fetch package.json from GitHub

For each application approved in Step 1:

```bash
gh api repos/OASIS/<<application>>/contents/package.json --jq '.content' | base64 -d
```

## oasis-fe-mono Dependency

If the application being migrated is **not** `oasis-fe-mono`, check whether it lists `oasis-fe-mono` as a dependency. If it does, resolve the latest published version and add it to the dependency table:

```bash
npm view oasis-fe-mono version
```

Add it with the note: `"Update to latest version published from migrated oasis-fe-mono"`.

## Resolve Target Versions from npm

For each Angular-related and peer dependency found, resolve the exact target version:

```bash
npm view <<package>>@<<version>> version
```

Version resolution patterns:

- **Packages that track Angular major** (e.g. `@angular/*`, `@angular-devkit/*`, `@schematics/angular`, `ng-packagr`):
  ```bash
  npm view <<package>>@<<major>> version | tail -1
  ```
- **Packages with own versioning** (e.g. `@ngxs/store`, `jest-preset-angular`, `typescript`, `@nx/angular`):
  ```bash
  npm view <<package>>@">=<<major>> <$(( <<major>> + 1 ))" version | tail -1
  ```
- **Already compatible packages**: note "no change needed"

## Dependency Table Format

Build a table with resolved versions:

| Package | Current Version | Required Version | Notes |
|---------|----------------|-----------------|-------|
| `@angular/core` (+ all `@angular/*`) | x.x.x | resolved | Via `nx migrate` or `ng update` |
| `@angular/cli` | x.x.x | resolved | Via `nx migrate` or `ng update` |
| `@angular-devkit/*` | x.x.x | resolved | Follows Angular CLI |
| `typescript` | x.x.x | resolved | Check Angular peer dep requirements |
| `zone.js` | x.x.x | resolved | Check peer dep requirements |
| ... | ... | ... | ... |

Flag packages with ⚠️ where the version relationship is unclear or needs manual verification (e.g. Nx, Storybook).

## Update Subtasks with Dependency Tables

Split dependencies into two groups and update the corresponding subtasks:

**Angular packages** (`@angular/`, `@angular-devkit/`, `@schematics/angular`):

```bash
jira issue list -P <<story-key>> --plain --columns key,summary | grep "Update Angular Version"
jira issue edit <<subtask-key>> -b"Angular packages to update:\n<<angular dependency table>>" --no-input
```

**All other dependencies** (`typescript`, `zone.js`, `@ngxs/*`, `@nx/*`, `jest-preset-angular`, `ng-packagr`, `@storybook/*`, etc.):

```bash
jira issue list -P <<story-key>> --plain --columns key,summary | grep "Update dependencies"
jira issue edit <<subtask-key>> -b"Dependencies to update:\n<<non-angular dependency table>>" --no-input
```

Repeat for all stories created in Step 3.
