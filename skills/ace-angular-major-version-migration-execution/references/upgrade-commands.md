# Upgrade Commands Reference

Detailed commands for Step 3 of the Angular major version migration. The detected package manager and project type (from Step 3 preamble) determine which variants to use throughout.

## Fix nx.json Package Manager (Nx monorepo only)

Before running the migration, ensure `nx.json` reflects the actual package manager in use:

```json
"cli": {
  "packageManager": "npm"
}
```

- If the project uses **pnpm** but `nx.json` says `"npm"`, change it to `"pnpm"`. Leaving it as `npm` causes `nx migrate --run-migrations` to fail with `Cannot read properties of null (reading 'matches')`.
- If the project uses **npm**, ensure it says `"npm"` (or is absent).

## Run the Migration

All Nx commands require `NX_SKIP_PROVENANCE_CHECK=true` due to a custom npm registry that blocks provenance checks.

**Nx monorepo (pnpm):**

```bash
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx migrate @angular/core@<<version>> @angular/cli@<<version>>
pnpm install
NX_SKIP_PROVENANCE_CHECK=true pnpm exec nx migrate --run-migrations
```

**Nx monorepo (npm):**

```bash
NX_SKIP_PROVENANCE_CHECK=true npx nx migrate @angular/core@<<version>> @angular/cli@<<version>>
npm install
NX_SKIP_PROVENANCE_CHECK=true npx nx migrate --run-migrations
```

**Standalone Angular CLI:**

```bash
ng update @angular/core@<<version>> @angular/cli@<<version>>
```

## Update Angular CLI and DevKit Packages (Nx monorepo)

`nx migrate` does **not** automatically update `@angular/cli` and `@angular-devkit/*` packages. Failing to do so causes: _"This version of CLI is only compatible with Angular versions ^<<previous>>..."_

`@angular-devkit/architect` uses a `0.<<major>><<minor>>.<<patch>>` version format (e.g. `0.1902.20` for Angular 19.2.20):

```bash
# pnpm
pnpm add --save-dev \
  @angular/cli@<<version>> \
  @angular-devkit/architect@<<devkit-architect-version>> \
  @angular-devkit/build-angular@<<version>> \
  @angular-devkit/core@<<version>> \
  @angular-devkit/schematics@<<version>> \
  @schematics/angular@<<version>>

# npm
npm install --save-dev \
  @angular/cli@<<version>> \
  @angular-devkit/architect@<<devkit-architect-version>> \
  @angular-devkit/build-angular@<<version>> \
  @angular-devkit/core@<<version>> \
  @angular-devkit/schematics@<<version>> \
  @schematics/angular@<<version>>
```

## Update Angular Ecosystem Packages

`nx migrate` only upgrades core Angular packages. `@angular/cdk`, `@angular/material`, and other `@angular`-scoped packages must be bumped manually.

Check which packages are still on the old major version:

```bash
grep '"@angular/' package.json | grep -v "<<version>>"
```

`@angular/cdk` and `@angular/material` use their own patch numbering independent of `@angular/core`. Use `pnpm view @angular/cdk versions` or `npm view @angular/cdk versions` to find the exact latest:

```bash
# pnpm
pnpm add @angular/cdk@<<cdk-version>>
# repeat for @angular/material and any other ecosystem packages

# npm
npm install @angular/cdk@<<cdk-version>>
```

## Update Remaining Dependencies

Read the dependency table from the `$SUB_UPDATE_DEPS` subtask first:

```bash
jira issue view $SUB_UPDATE_DEPS --plain
```

Then update each package to its required version:

```bash
# pnpm
pnpm add <<package>>@<<required-version>>

# npm
npm install <<package>>@<<required-version>>
```

After processing each package, update its row icon in the subtask description via the Jira REST API:

- `(/)` — updated successfully
- `(?)` — no update needed (already on required version)
- `(!)` — update produced warnings or errors

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]
# Replace ( ) with the appropriate icon for each row as you process it
payload = json.dumps({"fields": {"description": "<<updated-description-with-icons>>"}})
subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", payload,
    f"https://atc.bmwgroup.net/jira/rest/api/2/issue/{os.environ['SUB_UPDATE_DEPS']}"],
    capture_output=True, text=True)
```

## Install and Resolve

```bash
# pnpm
pnpm install

# npm
npm install
```

Review all peer dependency warnings and resolve them.

## Format Migration Changes with Prettier

The Angular migration schematics introduce inconsistent whitespace. Run Prettier across all changed files immediately after the migrations:

```bash
# pnpm
git diff --name-only | xargs pnpm exec prettier --write

# npm
git diff --name-only | xargs npx prettier --write
```

Then compile and fix any errors:

```bash
# pnpm
pnpm run build

# npm
npm run build
```

Address compilation errors one by one before continuing.
