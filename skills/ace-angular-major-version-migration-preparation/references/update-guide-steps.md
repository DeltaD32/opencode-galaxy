# Update Guide Steps Reference

Detailed script and Jira update pattern for Step 4 of the Angular major version migration preparation.

## Fetch Update Guide Steps via Playwright

Fetch all steps from `angular.dev/update-guide` at **Advanced** complexity (`l=3`), which shows all steps regardless of difficulty level:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://angular.dev/update-guide?v=<<current-major>>.0-<<major>>.0&l=3", wait_until="networkidle", timeout=30000)
    steps = page.query_selector_all(".adev-recommendation-content")
    for i, step in enumerate(steps):
        badge = step.query_selector(".adev-complexity-badge")
        complexity = badge.inner_text().strip() if badge else "?"
        text = step.inner_text().replace(complexity, "").strip()
        print(f"[{i+1}] [{complexity}] {text}")
    browser.close()
```

## Update Subtask Description via Jira REST API

Once the user has approved the step selection, update the **"Implement Angular Update Guide steps"** subtask on every story with the full table as description. Use a Python subprocess to avoid shell escaping issues with multi-line JSON:

```python
import subprocess, os, json

token = os.environ["JIRA_API_TOKEN"]
description = "||Done||#||Step||Level||Risk||Copilot Success %||\n|( )|1|...|Basic|Low|95%|\n..."
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
