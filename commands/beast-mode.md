---
description: "Autonomous execution with 3 self-correcting RALPH loops and zero interruptions. State assumptions and continue."
---

Execute the current task end-to-end with full autonomy. Rules:

1. **No interruptions.** Do not ask clarifying questions unless completely blocked with no reasonable assumption possible.
2. **State and continue.** When assumptions are needed, state them inline and proceed.
3. **3 RALPH loops.** If a step fails, retry up to 3 times with a different approach before reporting the failure.
4. **Quality gates.** After each major action: verify the output is correct before moving on.
5. **Lessons Learned (LeLe).** After the task completes, append a brief "Lessons Learned" section summarising what worked, what failed, and what to do differently next time.
6. **Smallest diff.** Code changes must be the minimal correct change — no refactors, no style changes, no unrelated edits.
7. **Zero regressions.** Run existing tests after code changes if a test runner is available.

Begin executing the task in the current session context immediately.
