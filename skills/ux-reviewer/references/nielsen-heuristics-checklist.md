# Nielsen Heuristics Checklist

Use this checklist during audits to avoid skipping heuristics and to keep findings specific.

## 1) Visibility Of System Status

Definition: Keep users informed about what is happening through timely and clear feedback.

Audit questions:

- Is loading, processing, or saving visible?
- Is success/failure feedback immediate and understandable?
- Are asynchronous actions clearly acknowledged?

Common failure signals:

- Silent clicks with no feedback
- Unclear loading states
- Success and error messages that disappear too quickly

## 2) Match Between System And The Real World

Definition: Use language, metaphors, and workflows that match users' mental models.

Audit questions:

- Does wording use domain terms users actually understand?
- Is the process order natural from a user perspective?
- Are units, formats, and labels familiar?

Common failure signals:

- Internal jargon in UI labels
- Workflow order that conflicts with real task order
- Ambiguous icons with no supporting labels

## 3) User Control And Freedom

Definition: Support undo, back, cancel, and safe exits from unintended actions.

Audit questions:

- Can users reverse or cancel major actions?
- Are destructive actions guarded and recoverable?
- Can users leave a flow without losing everything unexpectedly?

Common failure signals:

- No cancel/undo for risky actions
- Navigation traps in modal or multi-step flows
- Immediate destructive operations with no confirmation

## 4) Consistency And Standards

Definition: Follow platform conventions and keep internal patterns consistent.

Audit questions:

- Are common actions located and named consistently?
- Do components behave consistently across screens?
- Are platform conventions respected?

Common failure signals:

- Different labels for the same action
- Inconsistent error placement or button hierarchy
- Custom controls behaving unlike expected patterns

## 5) Error Prevention

Definition: Prevent mistakes before they happen through constraints, defaults, and guidance.

Audit questions:

- Does the interface prevent invalid input early?
- Are defaults safe and sensible?
- Are risky actions separated from routine actions?

Common failure signals:

- Validation only after submit
- Easy-to-trigger destructive actions
- Missing guardrails for irreversible choices

## 6) Recognition Rather Than Recall

Definition: Minimize memory load by making options and context visible.

Audit questions:

- Are key options and next steps visible without memory burden?
- Is context preserved across steps?
- Are labels and hints present when needed?

Common failure signals:

- Users must remember values across screens
- Hidden options only discoverable by trial and error
- Missing contextual clues in forms and filters

## 7) Flexibility And Efficiency Of Use

Definition: Support both novice and expert workflows.

Audit questions:

- Are there shortcuts or accelerators for frequent tasks?
- Can users complete tasks efficiently at scale?
- Are repetitive steps minimized?

Common failure signals:

- Excessive clicks for common tasks
- No batch actions where expected
- Forced linear flow for advanced users

## 8) Aesthetic And Minimalist Design

Definition: Show only relevant information and controls needed for the task.

Audit questions:

- Is each screen focused on a clear primary task?
- Is visual noise competing with important content?
- Are secondary actions deprioritized appropriately?

Common failure signals:

- Overloaded forms or dashboards
- Primary CTA visually diluted
- Dense copy without hierarchy

## 9) Help Users Recognize, Diagnose, And Recover From Errors

Definition: Error messages should be clear, specific, and actionable.

Audit questions:

- Do errors explain what happened and how to fix it?
- Are messages located near the relevant field/action?
- Is recovery path obvious and low friction?

Common failure signals:

- Generic "Something went wrong" messages
- Errors disconnected from the problematic field
- No guidance for recovery

## 10) Help And Documentation

Definition: Provide accessible help when needed, even if the system is easy to use.

Audit questions:

- Is contextual help available at the point of need?
- Is support information searchable and concise?
- Are onboarding and advanced docs easy to find?

Common failure signals:

- Missing in-flow guidance for uncommon tasks
- Help content hidden or outdated
- No link between error states and relevant help

## Severity Calibration Tips

When assigning severity, consider:

- Frequency: how often users hit this issue
- Impact: how much it harms task success
- Persistence: whether users can recover easily

Use confidence levels when evidence is incomplete and clearly call out assumptions.
