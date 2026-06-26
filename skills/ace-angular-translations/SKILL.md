---
name: ace-angular-translations
description: >-
  Enforce common-first i18n policy: check oasis-fe-mono common translations before adding app-specific keys. Triggers in any Angular app.
metadata:
  version: '1.1.0'
  authors:
    - name: Matthijs Vliegenthart
      email: matthijsvliegenthart@partner.bmwgroup.com
  tags:
    - angular
    - i18n
    - translations
    - oasis-fe-mono
---

# Translation Management for oasis-fe-mono

**Never add a translation key to an app-specific file if it already exists in the common translation files.**

- Common: `libs/core-components/src/lib/core-translate/locale/<lang>.common.json`
- App-specific: `apps/<app-name>/src/assets/i18n/<lang>.app.json`

## Workflow

### Step 1: Search Common Files First

Before adding any key, search `libs/core-components/src/lib/core-translate/locale/en.common.json` for:
1. The exact key you intend to add
2. Similar keys that convey the same meaning (e.g., `close` vs `button-close`)
3. The English value — another key may already map to the same text

If a match exists: use that key directly. Do **not** duplicate it in the app-specific file.

### Step 2: Add to App-Specific File Only When Absent

Only when the key is **not present** in common files, add it to `apps/<app-name>/src/assets/i18n/<lang>.app.json`.

### Step 3: Follow Key Conventions

- **Kebab-case, lowercase** only (e.g., `search-customer-branch`), except for enum values — use the enum value name as-is for the key
- Key as **close to the English translation as possible** (e.g., "Download" button → `download`, not `quote-summary-download-button`)
- **Omit** keys for languages without a translation — English fallback is automatic
- Do **not** put English text in non-English files (e.g., no English values in `es.app.json`)
