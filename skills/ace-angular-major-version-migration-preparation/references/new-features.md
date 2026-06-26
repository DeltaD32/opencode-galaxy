# New Angular Features Reference

Detailed script and Jira update pattern for Step 5 of the Angular major version migration preparation.

## Fetch New Features via Playwright

Fetch features from `https://angular.love/angular-<<major>>-whats-new` for each version to cover. Do **not** use any other source.

If migrating more than one major version (e.g. from v17 to v19), fetch features for **each intermediate and target version** (e.g. v18 and v19) and combine into a single table grouped by version:

```python
from playwright.sync_api import sync_playwright

# List all versions to cover, e.g. [18, 19] when migrating from 17 to 19
versions_to_fetch = list(range(<<current-major>> + 1, <<major>> + 1))

def fetch_features(page, major):
    page.goto(f"https://angular.love/angular-{major}-whats-new", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    return page.evaluate("""() => {
        const results = [];
        const headings = document.querySelectorAll('article h2, article h3');
        const skip = ['Summary','Sign up for our newsletter','Main partner','Community partners'];
        headings.forEach(h => {
            const title = h.innerText.trim();
            if (skip.includes(title)) return;
            let desc = '';
            let el = h.nextElementSibling;
            while (el && !['H2','H3'].includes(el.tagName)) {
                if (el.tagName === 'P') desc += el.innerText.trim() + ' ';
                el = el.nextElementSibling;
            }
            results.push({title, desc: desc.trim().slice(0, 200)});
        });
        return results;
    }""")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    all_features = {}
    for major in versions_to_fetch:
        all_features[major] = fetch_features(page, major)
        print(f"\n--- Angular {major} ({len(all_features[major])} features) ---")
        for i, f in enumerate(all_features[major]):
            print(f"  [{i+1}] {f['title']}: {f['desc'][:100]}")
    browser.close()
```

## Update Subtask Description via Jira REST API

Once the user has approved the feature selection, update the **"Implement New Angular Version features"** subtask on every story with the full table as description:

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]
description = "||Done||#||Version||Feature||Risk||Copilot Success %||\n|( )|1|Angular X|...|Low|95%|\n..."
payload = json.dumps({"fields": {"description": description}})
subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-X", "PUT",
    "-H", f"Authorization: Bearer {token}",
    "-H", "Content-Type: application/json",
    "-d", payload,
    f"https://atc.bmwgroup.net/jira/rest/api/2/issue/<<subtask-key>>"],
    capture_output=True, text=True)
```

Repeat for all stories created in Step 3.

### Jira Wiki Markup Notes

- Use `||header||` for header cells, `|cell|` for data cells.
- Each row starts with `|( )|` as an unchecked icon.
- During migration execution, update completed rows from `( )` to `(/)` by re-issuing this PUT call with the updated description.
