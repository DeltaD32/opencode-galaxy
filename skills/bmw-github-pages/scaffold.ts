#!/usr/bin/env npx tsx

/**
 * scaffold.ts
 *
 * Cross-platform scaffold script for creating BMW-styled static sites
 * with GitHub Pages deployment.
 *
 * Usage:
 *   npx tsx scaffold.ts --name "my-project" --dir ./my-project
 *   npx tsx scaffold.ts --name "my-project" --dir ./my-project --description "A cool project"
 */

import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync, copyFileSync } from "fs";
import { join, resolve, dirname, relative } from "path";
import { fileURLToPath } from "url";
import { parseArgs } from "util";

const TEMPLATES_DIR = join(dirname(fileURLToPath(import.meta.url)), "templates");

interface ScaffoldOptions {
  name: string;
  dir: string;
  description?: string;
  subtitle?: string;
  organization?: string;
}

function copyDirSync(src: string, dest: string): void {
  mkdirSync(dest, { recursive: true });
  const entries = readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = join(src, entry.name);
    const destPath = join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      copyFileSync(srcPath, destPath);
    }
  }
}

function listFiles(dir: string, base: string = dir): string[] {
  const files: string[] = [];
  const entries = readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...listFiles(fullPath, base));
    } else {
      files.push(relative(base, fullPath));
    }
  }
  return files;
}

function scaffold(options: ScaffoldOptions): void {
  const { name, dir, description, subtitle, organization } = options;
  const targetDir = resolve(dir);

  console.log(`\nScaffolding BMW static site: ${name}`);
  console.log(`  Target: ${targetDir}\n`);

  // Validate templates directory exists
  if (!existsSync(TEMPLATES_DIR)) {
    console.error(`Error: Templates directory not found at ${TEMPLATES_DIR}`);
    process.exit(1);
  }

  // Create target directory
  if (existsSync(targetDir)) {
    const entries = readdirSync(targetDir);
    if (entries.length > 0) {
      console.error(`Error: Target directory is not empty: ${targetDir}`);
      process.exit(1);
    }
  }
  mkdirSync(targetDir, { recursive: true });

  // Copy all template files
  console.log("Copying template files...");
  copyDirSync(TEMPLATES_DIR, targetDir);

  // Customize site.json with user's project details
  const siteJsonPath = join(targetDir, "site.json");
  if (existsSync(siteJsonPath)) {
    let config: any;
    try {
      config = JSON.parse(readFileSync(siteJsonPath, "utf8"));
    } catch (err) {
      console.error(`Error: Failed to parse ${siteJsonPath}`);
      console.error(`  ${err instanceof Error ? err.message : err}`);
      process.exit(1);
    }

    if (!config.site || !config.hero) {
      console.error(`Error: site.json is missing required top-level keys ('site' and/or 'hero').`);
      process.exit(1);
    }

    config.site.name = name;
    if (subtitle) config.site.subtitle = subtitle;
    if (description) config.site.description = description;
    if (organization) config.site.organization = organization;

    // Update hero to match
    config.hero.heading = name;
    if (description) config.hero.tagline = description;

    writeFileSync(siteJsonPath, JSON.stringify(config, null, 2) + "\n");
    console.log("  Updated site.json with project details");
  }

  // List created files
  const files = listFiles(targetDir);
  console.log(`\nCreated ${files.length} files:`);
  for (const file of files.sort()) {
    console.log(`  ${file}`);
  }

  console.log(`
Done! Next steps:

  1. cd ${relative(process.cwd(), targetDir) || "."}
  2. npm install
  3. npm run build
  4. npm run dev          # preview locally

To deploy to GitHub Pages:
  1. Create a GitHub repo
  2. git init && git add -A && git commit -m "Initial scaffold"
  3. git remote add origin <repo-url>
  4. git push -u origin main
  5. Enable GitHub Pages in repo settings (Source: GitHub Actions)
`);
}

// --- CLI entry point ---

const { values } = parseArgs({
  options: {
    name: { type: "string", short: "n" },
    dir: { type: "string", short: "d" },
    description: { type: "string" },
    subtitle: { type: "string" },
    organization: { type: "string", short: "o" },
    help: { type: "boolean", short: "h" },
  },
  strict: true,
});

if (values.help) {
  console.log(`
BMW GitHub Pages Scaffold

Usage:
  npx tsx scaffold.ts --name <project-name> --dir <target-directory>

Options:
  -n, --name           Project name (required)
  -d, --dir            Target directory (required)
  --description        Project description
  --subtitle           Project subtitle (shown in header)
  -o, --organization   Organization name (default: "BMW Group")
  -h, --help           Show this help message
`);
  process.exit(0);
}

if (!values.name || !values.dir) {
  console.error("Error: --name and --dir are required. Use --help for usage information.");
  process.exit(1);
}

scaffold({
  name: values.name,
  dir: values.dir,
  description: values.description,
  subtitle: values.subtitle,
  organization: values.organization,
});
