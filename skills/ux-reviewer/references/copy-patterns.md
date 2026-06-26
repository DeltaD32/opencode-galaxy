# UX Writing Copy Patterns

This reference provides **ready-to-use patterns and templates** for common UI components and scenarios. Use this as a **quick reference library** when writing or evaluating interface copy.

**For evaluation methodology** (how to audit content using the 6 UX writing principles), see [`ux-writing-evaluation-guide.md`](ux-writing-evaluation-guide.md).

## Table of Contents

1. [Microcopy Quick Reference](#microcopy-quick-reference)
2. [Buttons and CTAs](#buttons-and-ctas)
3. [Error Messages](#error-messages)
4. [Success and Confirmation Messages](#success-and-confirmation-messages)
5. [Form Fields](#form-fields)
6. [Empty States](#empty-states)
7. [Loading and Progress](#loading-and-progress)
8. [Tooltips and Helper Text](#tooltips-and-helper-text)
9. [Navigation and Labels](#navigation-and-labels)
10. [Notifications](#notifications)
11. [Onboarding](#onboarding)
12. [Confirmations and Dialogs](#confirmations-and-dialogs)
13. [Search and Filtering](#search-and-filtering)

---

## Microcopy Quick Reference

Microcopy refers to the small bits of text throughout your interface that guide users and help them complete tasks.

### Button Labels

- **Action-oriented**: Start with a verb
- **Specific**: "Create account" not "Submit"
- **Outcome-focused**: "Download report" not "Click here"
- **Match user intent**: What users want to do, not what the business wants

### Form Labels

- **Clear and concise**: No unnecessary words
- **No jargon**: Use plain language
- **Descriptive**: "Email address" not "Email"
- **Positioned above the field**: Ensures visibility

### Tooltips

- **Brief explanations**: Under 2 sentences
- **For complex features**: Only when truly needed
- **Provide context**: Not instructions
- **Example**: "API Key: Unique identifier for authenticating requests"

### Placeholder Text

- **Example format**: Show what goes in the field
- **Not instructions**: "name@example.com" not "Enter your email"
- **Realistic examples**: Use actual example data
- **Don't replace labels**: Placeholders disappear when typing

### Error Messages

- **Say what happened**: "Payment declined"
- **Say why** (if helpful): "Your card was declined by your bank"
- **Say what to do next**: "Try a different card or contact your bank"
- **Human tone**: Not robotic or blaming

### Empty States

- **Explain what will appear**: "Projects will appear here"
- **Guide to action**: "Create your first project"
- **Encouraging tone**: Helpful, not negative
- **Clear CTA**: Specific next step

### Confirmation Messages

- **Confirm what happened**: "Changes saved"
- **Provide next steps**: "View your profile"
- **Include undo option**: For reversible actions
- **Brief and positive**: Short, encouraging

### Onboarding Copy

- **Welcome without overwhelming**: Keep it simple
- **One concept at a time**: Don't introduce multiple features at once
- **Action-oriented**: Do, not just read
- **Allow skipping**: Don't force users through everything

---

## Buttons and CTAs

### Primary Actions

**Pattern**: `[Verb] + [Noun]`

**Examples**:

- Create account
- Save changes
- Send message
- Download report
- Start trial
- Upload file
- Add member
- Delete permanently

**Guidelines**:

- Start with a verb (create, save, send, not "submit")
- Be specific about the outcome
- Include what's being acted upon
- Match user intent (not business intent)
- Primary CTA should be the most common action
- Keep under 25 characters
- Use sentence case

### Secondary Actions

**Examples**:

- Cancel
- Not now
- Skip
- Go back
- Learn more
- View details

**Guidelines**:

- Brief but clear
- Non-committal for dismissible actions
- Match tone to primary action

### Destructive Actions

**Pattern**: `[Action] [permanently/forever]`

**Examples**:

- Delete permanently
- Cancel subscription
- Remove member
- Clear all data

**Guidelines**:

- Be explicit about consequences
- Use red/warning styling
- Require confirmation
- Use "permanently" when irreversible

### Text Links

**Examples**:

- View pricing details (not "click here")
- Read our privacy policy (not "learn more")
- Contact support (not "need help")

**Guidelines**:

- Link text should describe the destination
- Should make sense out of context
- Avoid generic "click here" or "read more"

---

## Error Messages

### Template

```
[What went wrong] [Why it matters - optional] [What to do next]
```

### Form Validation Errors

**Email**:

- ❌ "Invalid email"
- ✅ "Email must include '@' symbol"
- ✅ "Enter a valid email address"

**Password**:

- ❌ "Wrong password"
- ✅ "Password must be at least 8 characters"
- ✅ "Password must include a number"
- ✅ "Passwords don't match"

**Required Fields**:

- ❌ "This field is required"
- ✅ "Name is required"
- ✅ "Email required. Enter your email to continue"

**Username**:

- ✅ "Username must be 3-20 characters"
- ✅ "Username already taken. Try another"
- ✅ "Username can only contain letters and numbers"

**Phone Number**:

- ✅ "Phone number must be 10 digits"
- ✅ "Enter phone number in format: +1 (555) 555-5555"

### File Upload Errors

- ✅ "File size must be under 10 MB"
- ✅ "Only .jpg, .png, and .pdf files are supported"
- ✅ "Upload failed. Check your connection and try again"
- ✅ "Maximum 5 files allowed"

### Connection Errors

- ✅ "No internet connection. Check your connection and try again"
- ✅ "Request timeout. Try again"
- ✅ "Could not connect to server. Try again later"

### Permission Errors

- ✅ "You don't have permission to access this page"
- ✅ "Admin access required to continue"
- ✅ "This feature is only available on premium plans. Upgrade to access"

### Not Found Errors

- ✅ "Page not found. Return to dashboard"
- ✅ "File not found. Check the file name and try again"
- ✅ "User not found. Check the email address"

### System Errors

- ✅ "Something went wrong. Try again"
- ✅ "We're experiencing technical difficulties. Try again in a few minutes"
- ✅ "Service temporarily unavailable. We're working to fix this"

### Payment and Transaction Errors

**Payment Declined**:

- ✅ "Payment declined. Your card was declined by your bank. Try a different card or contact your bank."
- ✅ "Payment failed. Check your card details and try again."
- ✅ "Transaction declined. Your payment method couldn't be charged. Update your payment method."

**Insufficient Funds**:

- ✅ "Payment failed. Insufficient funds. Try a different payment method."

**Expired Card**:

- ✅ "Payment failed. Your card has expired. Add a new card to continue."

**Guidelines**:

- Say what happened (clear, not technical)
- Say why (if helpful and brief)
- Say what to do next (specific action)
- Use a human tone (not robotic or blaming)
- Never blame the user
- Be specific about the problem
- Provide actionable solutions
- Use empathetic, helpful tone
- Avoid error codes unless necessary
- If showing error code, explain it in plain language

---

## Success and Confirmation Messages

### Completion Messages

**Pattern**: `[Action completed] [result - optional]`

**Examples**:

- ✅ "Changes saved"
- ✅ "Message sent"
- ✅ "Account created successfully"
- ✅ "File uploaded"
- ✅ "Payment processed. Check your email for confirmation"
- ✅ "Invitation sent to john@example.com"

### Next Step Suggestions

**Examples**:

- ✅ "Profile updated. View your profile"
- ✅ "Project created. Add your first task"
- ✅ "Account verified. Start exploring"

**Guidelines**:

- Confirm what just happened
- Be brief but warm and positive
- Provide next steps if relevant
- Include undo option for reversible actions (e.g., "Undo" link)
- Use encouraging tone
- Don't overuse "successfully"

**With Undo Option**:

- ✅ "File deleted. [Undo]"
- ✅ "3 items removed from cart. [Undo]"
- ✅ "Message archived. [Undo]"

---

## Form Fields

### Labels

**Examples**:

- Email address
- Full name
- Phone number
- Password
- Confirm password
- Company name

**Guidelines**:

- Use sentence case
- Be specific and descriptive
- Position above the field for visibility
- No colons needed
- Keep to 1-3 words when possible

### Placeholders

**Examples**:

- name@example.com (for email)
- +1 (555) 555-5555 (for phone)
- Enter your message (for textarea)
- Search projects (for search)

**Guidelines**:

- Show format or example
- Don't repeat the label
- Use realistic examples
- Don't use for critical information
- Keep brief
- Lower priority than labels

### Helper Text

**Examples**:

- "Your email won't be shared publicly"
- "Must be at least 8 characters with one number"
- "We'll use this to contact you about your order"
- "Choose a unique username others can search"

**Guidelines**:

- Provide context labels don't cover
- Keep under 2 sentences
- Place below the field
- Only include if truly helpful
- Don't state the obvious

### Required Field Indicators

**Examples**:

- Mark with asterisk (_) and legend: "_ Required"
- Use "(required)" after label
- Use "(optional)" for optional fields when most are required

**Guidelines**:

- Be consistent throughout the form
- Explain required field indicator
- Consider marking optional instead if most are required

---

## Empty States

### Pattern

```
[Acknowledge state] [Why empty - optional] [Call to action]
```

### First-Use Empty States

**Examples**:

- ✅ "No projects yet. Create your first project to get started"
- ✅ "No projects yet. Create your first project to start collaborating with your team"
- ✅ "Your inbox is empty. Messages will appear here"
- ✅ "No team members. Invite your team to collaborate"

### User-Cleared Empty States

**Examples**:

- ✅ "All tasks complete! You're all caught up"
- ✅ "Trash is empty"
- ✅ "No archived items"

### Search/Filter Empty States

**Examples**:

- ✅ "No results found. Try a different search term"
- ✅ "No projects match your filters. Clear filters to see all projects"
- ✅ "We couldn't find any matches for 'design'"

### Error Empty States

**Examples**:

- ✅ "Couldn't load messages. Check your connection and try again"
- ✅ "Something went wrong. Refresh to try again"

**Guidelines**:

- Explain what will appear here
- Guide the user to take action
- Use an encouraging, helpful tone
- Provide a clear CTA
- Acknowledge the empty state
- Be encouraging, not negative
- Use illustrations when helpful
- Explain why empty when unclear

---

## Loading and Progress

### Loading States

**Short wait** (< 3 seconds):

- "Loading..."
- "Saving..."
- "Processing..."

**Long wait** (> 3 seconds):

- "This may take a moment..."
- "Uploading large file..."
- "Generating report..."

**Unknown duration**:

- "Loading your data..."
- "Setting up your account..."

### Progress Indicators

**With percentage**:

- "Uploading... 60%"
- "3 of 10 images processed"

**Multi-step**:

- "Step 2 of 4: Processing payment"
- "Creating your account..."
- "Almost done..."

**Guidelines**:

- Keep users informed
- Set expectations for long waits
- Show progress when possible
- Use present continuous tense (-ing)
- Be specific about what's happening

---

## Tooltips and Helper Text

### Informational Tooltips

**Examples**:

- 📊 Stats: "Total views in the last 30 days"
- ℹ️ Feature: "Premium feature. Upgrade to access"
- 🔒 Privacy: "Only visible to you"

### Action Tooltips (Icon Buttons)

**Examples**:

- Edit
- Delete
- Download
- Share
- Copy link
- Mark as complete

### Definition Tooltips

**Examples**:

- "API Key: Unique identifier for authenticating requests"
- "Bounce rate: Percentage of visitors who leave after viewing one page"

**Guidelines**:

- Keep under 2 sentences
- Don't repeat visible text
- Only include if needed
- Provide context, not instructions

---

## Navigation and Labels

### Main Navigation

**Examples**:

- Dashboard
- Projects
- Messages
- Settings
- Help

**Guidelines**:

- Use familiar, scannable terms
- Keep to 1-2 words
- Use consistent terminology
- Prioritize by user tasks

### Breadcrumbs

**Examples**:

- Home > Projects > Project name
- Dashboard > Settings > Profile

**Guidelines**:

- Show hierarchy
- Make each level clickable except current
- Use > or / as separators

### Tabs

**Examples**:

- Overview
- Activity
- Members
- Settings

**Guidelines**:

- Parallel structure
- Clear and distinct
- 1-2 words each

---

## Notifications

### In-App Notifications

**Success**:

- ✅ "Changes saved"
- ✅ "Member added"

**Info**:

- ℹ️ "New version available. Update now"
- ℹ️ "Your trial ends in 3 days"

**Warning**:

- ⚠️ "Your session will expire in 5 minutes"
- ⚠️ "Low storage space. Upgrade or delete files"

**Error**:

- ❌ "Payment failed. Update your payment method"
- ❌ "Connection lost. Reconnecting..."

### Push Notifications

**Examples**:

- "You have 3 new messages"
- "Sarah mentioned you in a comment"
- "Report ready to download"

**Guidelines**:

- Lead with most important information
- Be specific and actionable
- Keep under 50 characters when possible
- Include sender/source when relevant

---

## Onboarding

### Welcome Messages

**Examples**:

- "Welcome to [Product]! Let's get you set up"
- "Thanks for joining! Here's what to do first"

### Step Instructions

**Examples**:

- "Step 1: Create your profile"
- "Add your first project"
- "Invite your team (optional)"

### Completion Messages

**Examples**:

- "You're all set! Start exploring"
- "Setup complete. Here's your dashboard"

**Guidelines**:

- Welcome without overwhelming
- One concept at a time (don't introduce multiple features in one step)
- Action-oriented (do, not just read)
- Break into small steps
- Show progress
- Make skippable when possible
- Celebrate completion

---

## Confirmations and Dialogs

### Destructive Action Confirmations

**Pattern**:

```
Heading: [Action]?
Body: [Consequence] [Additional context]
Primary button: [Confirm action]
Secondary button: Cancel
```

**Examples**:

**Delete confirmation**:

```
Heading: "Delete project?"
Body: "This action cannot be undone. All project data will be permanently deleted."
Primary: "Delete permanently"
Secondary: "Cancel"
```

**Delete multiple files**:

```
Heading: "Delete 3 files?"
Body: "This can't be undone."
Primary: "Delete files"
Secondary: "Keep files"
```

**Cancel subscription**:

```
Heading: "Cancel subscription?"
Body: "You'll lose access to premium features at the end of your billing period."
Primary: "Cancel subscription"
Secondary: "Keep subscription"
```

### Non-Destructive Confirmations

**Discard changes**:

```
Heading: "Discard unsaved changes?"
Primary: "Discard"
Secondary: "Keep editing"
```

**Log out**:

```
Heading: "Log out?"
Primary: "Log out"
Secondary: "Cancel"
```

**Guidelines**:

- Make the action clear and specific: "Delete 3 files?" not "Are you sure?"
- Include quantities when relevant: "Delete 3 items" not "Delete items"
- Describe consequences: "This can't be undone" or "This action cannot be undone"
- Label buttons with the action: "Delete files" / "Keep files" not "OK" / "Cancel"
- Be explicit about what will happen
- Use clear, specific language
- Make the safe choice the secondary action
- Don't use "OK" or "Yes/No" for destructive actions

**Common Patterns to Avoid**:

- ❌ "Are you sure?" - Too vague, doesn't describe the action
- ❌ "OK" / "Cancel" - Use specific action labels instead
- ❌ "Yes" / "No" - Not descriptive enough for important actions

---

## Search and Filtering

### Search Placeholders

**Examples**:

- "Search projects"
- "Find a contact"
- "Search by name or email"

### Search Results

**Examples**:

- "47 results for 'design'"
- "No results for 'xyz'. Try a different search"
- "Showing 10 of 127 results"

### Filters

**Examples**:

- "Filter by status"
- "All projects (47)"
- "Active filters: Status, Date"
- "Clear all filters"

### Sort Options

**Examples**:

- "Sort by: Newest first"
- "Sort by: Name (A-Z)"
- "Sort by: Most recent"

**Guidelines**:

- Show result count
- Provide clear "no results" messaging
- Make filters discoverable
- Allow easy clearing of filters
- Show active filters

---

## Quick Reference: Common Mistakes to Avoid

| ❌ Don't                      | ✅ Do                                        |
| ----------------------------- | -------------------------------------------- |
| "Click here"                  | "View pricing details"                       |
| "Submit"                      | "Create account"                             |
| "Error"                       | "Email must include '@' symbol"              |
| "Success"                     | "Changes saved"                              |
| "Invalid input"               | "Username must be 3-20 characters"           |
| "Please enter your email"     | "Enter your email"                           |
| "Are you sure?"               | "Delete project?"                            |
| "OK"                          | "Delete permanently" or "Save changes"       |
| "No data"                     | "No projects yet. Create your first project" |
| "Loading..." (for long waits) | "This may take a moment"                     |

---

## Character Count Guidelines

| Element         | Recommended Max | Notes                           |
| --------------- | --------------- | ------------------------------- |
| Button label    | 25 characters   | Shorter is better               |
| Page title      | 60 characters   | For SEO and display             |
| Error message   | 120 characters  | Should fit on one/two lines     |
| Success message | 60 characters   | Brief confirmation              |
| Tooltip         | 140 characters  | About 2 sentences               |
| Empty state     | 200 characters  | Includes headline + description |
| Notification    | 100 characters  | Must be scannable               |
| Form label      | 30 characters   | Keep to 1-3 words               |
| Placeholder     | 40 characters   | Example or format               |

---

## Best Practices Summary

1. **Be specific**: "Save changes" not "Submit"
2. **Be concise**: Remove unnecessary words
3. **Be helpful**: Provide next steps and solutions
4. **Be consistent**: Use same terms throughout
5. **Be human**: Empathetic and user-focused
6. **Be clear**: Front-load important information
7. **Be positive**: Frame constructively when possible

---

**Use this reference** when writing copy for specific components. Adapt patterns to match your specific context and brand voice while maintaining clarity and usability.
