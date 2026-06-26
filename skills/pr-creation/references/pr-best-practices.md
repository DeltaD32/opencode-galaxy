# Pull Request Best Practices

## Title Guidelines

- Start with a verb in imperative mood: "Add", "Fix", "Update", "Remove"
- Keep it under 72 characters
- Be specific: "Fix authentication timeout" not "Fix bug"
- Match conventional commit format when applicable: `feat:`, `fix:`, `docs:`, `chore:`

## Description Structure

### Summary Section

- 2-3 sentences maximum
- Answer: What changed and why?
- Focus on user/business value, not implementation details

**Good:**

```
Adds rate limiting to the API to prevent abuse. Users making more than
100 requests per minute will receive a 429 response with retry information.
```

**Bad:**

```
This PR updates the middleware stack to include a new RateLimitMiddleware
class that implements the TokenBucket algorithm with Redis backend storage.
```

### What Changed Section

- Use bullet points
- One change per bullet
- Group related changes together
- Order from most to least significant

**Good:**

- Added rate limiting middleware with 100 req/min limit
- Created Redis-backed token bucket implementation
- Added rate limit headers to API responses
- Updated API documentation with rate limit info

### How to Test Section

- Provide reproducible steps
- Include expected outcomes
- Add sample commands or requests when applicable
- Mention prerequisites (test accounts, data setup, etc.)

**Example:**

````markdown
## How to test

1. Start the development server: `npm run dev`
2. Make 101 requests to `/api/users` within one minute:

   ```bash
   for i in {1..101}; do curl http://localhost:3000/api/users; done
   ```

3. Verify the 101st request returns status 429
4. Check response headers include `X-RateLimit-Remaining: 0`
````

## Checklist Guidelines

- Only check items you've actually done
- Add custom checklist items for special requirements
- Explain any unchecked items in Notes section
- Common items:
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] Breaking changes documented
  - [ ] Migration guide provided (if applicable)

## Notes Section

Use this for:

- Context that doesn't fit elsewhere
- Known limitations or trade-offs
- Follow-up work needed
- Related PRs or issues
- Performance implications
- Security considerations

## Common Mistakes to Avoid

| Mistake                     | Impact                   | Fix                                |
| --------------------------- | ------------------------ | ---------------------------------- |
| Vague titles like "Updates" | Hard to scan PR list     | Be specific about what was updated |
| Wall of text descriptions   | Nobody reads them        | Use bullet points and sections     |
| No testing instructions     | Reviewers can't validate | Add clear reproduction steps       |
| Missing "why" context       | Changes seem arbitrary   | Explain the motivation             |
| Multiple unrelated changes  | Hard to review, risky    | Split into separate PRs            |

## Size Guidelines

- Small PRs (< 200 lines): Ideal, easy to review
- Medium PRs (200-500 lines): Acceptable, may need more context
- Large PRs (> 500 lines): Should be split unless unavoidable

When large PRs are necessary:

- Add a detailed description
- Break review into logical sections
- Consider draft PR for early feedback
- Highlight critical changes

```

```
