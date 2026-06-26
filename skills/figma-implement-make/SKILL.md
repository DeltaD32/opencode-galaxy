---
name: figma-implement-make
description: Translates Figma Make prototype code into production-ready code. Use when implementing UI from Figma Make files, when user mentions "implement design", "generate code", "implement component", "build Figma Make", provides Figma Make URLs (starting with https://www.figma.com/make/), or asks to build components matching Figma Make. Requires Figma MCP server connection.
compatibility: Requires Figma MCP server
metadata:
  tags:
    - Figma
    - Make
    - Frontend
    - UI
    - SCSS
    - HTML
  authors:
    - Jan Pohlmann <jan.pohlmann@bmw.de>
  version: "1.0.1"
---

# Implement Design

## Overview

This skill provides a structured workflow for translating Figma Make prototypes into production-ready code with pixel-perfect accuracy. It ensures consistent integration with the Figma MCP server, proper use of design tokens, and 1:1 visual parity with designs.

## Prerequisites

- Figma MCP server must be connected and accessible
  - Before proceeding, verify the Figma MCP server is connected by checking if Figma MCP tools (e.g., `get_design_context`) are available.
  - If the tools are not available, the Figma MCP server may not be enabled. Guide the user to enable the Figma MCP server that is included with the plugin. They may need to restart their MCP client afterward.
- User must provide a Figma URL in the format: `https://www.figma.com/make/:fileKey/:fileName?*`
  - `:fileKey` is the file key
- Project should have an established design system or component library (preferred)

## Required Workflow

**Follow these steps in order. Do not skip steps.**

### Step 1: Extract File Key from URL

Parse the Figma Make URL to extract the file key.

**URL format:** `https://www.figma.com/make/:fileKey/:fileName?*`

- **File key** = the segment immediately after `/make/`

**Example:**

- URL: `https://www.figma.com/make/1oP0cLPRq544kb13QSvPPM/Make-Template--Copy-?p=f&t=SXPjXXTcZTlDpvuJ-0&preview-route=%2Fbug-report`
- File key: `1oP0cLPRq544kb13QSvPPM`

### Step 2: Fetch Design Context via Figma MCP

Call `get_design_context` with the extracted file key and an empty node ID:

```
get_design_context(fileKey=":fileKey", nodeId="")
```

This returns resource links for all source files in the Figma Make project. Start by reading `App.tsx` to understand the overall structure, routing, and entry point.

### Step 3: Locate the Relevant Prototype Code

Using information from the user's prompt (page name, route, component name), navigate the Make prototype's file tree to find the specific page or component to implement.

- Check the route configuration in `App.tsx` for path mappings
- Follow imports to locate page-level and nested components
- Read through all relevant source files to understand the full structure, props, state, and behavior

### Step 4: Understand the Target Project

Before writing any code, analyze the target project:

- **Framework & language** (Angular, React, Vue, etc.)
- **Existing component library / design system** — check for an installed UI component library or design system. If there is one, check for available skills (e.g., <skill>density</skill>) and MCP servers that provide information about the design system.
- **Routing patterns** — how routes are defined and lazy-loaded
- **State management** — signals, services, stores, etc.
- **Styling approach** — CSS modules, SCSS, Tailwind, design tokens, etc.
- **File naming & folder conventions** — kebab-case, feature folders, etc.

### Step 5: Map Figma Make Components to Project Equivalents

Create a mental mapping between the Make prototype and the project:

| Make Prototype               | Target Project                                     |
| ---------------------------- | -------------------------------------------------- |
| React components             | Project framework components                       |
| Tailwind classes             | Project design tokens / CSS approach               |
| Inline styles                | Design system spacing, color, typography tokens    |
| Custom components            | Existing design system components where possible   |
| React Router routes          | Project routing mechanism                          |
| React state (useState, etc.) | Project state management (signals, services, etc.) |

### Step 6: Implement the Code

Translate the Make prototype into production code following these principles:

- **Design system first** — reuse existing components (buttons, inputs, cards, layouts) instead of recreating from scratch
- **No new CSS when avoidable** — rely on design system component styling; only write custom CSS when no existing token or component covers the need
- **Map tokens, not values** — translate Figma colors, spacing, and typography to project design tokens. Never hardcode hex values or pixel sizes when tokens exist.
- **Respect project conventions** — follow existing routing, state management, data-fetching, and file organization patterns
- **Accessibility** — follow WCAG guidelines: semantic HTML, labels, keyboard navigation, ARIA attributes where needed
- **Incremental approach** — build layout skeleton first, then populate sections one at a time, validating as you go

### Step 7: Integrate with the Project

- Add routes if implementing a new page
- Update navigation components if applicable
- Wire up any required services, API calls, or state
- Ensure the new code follows the project's module/import structure

### Step 8: Validate the Implementation

- Verify the implementation matches the Figma Make prototype and includes all the content requested by the user
- Check that all interactive behaviors (forms, buttons, navigation) work correctly
- Confirm accessibility requirements are met
- Ensure no lint or type errors exist
- Verify that the project builds without errors

## Examples

### Example 1: Implementing a page

User says: "Implement the /bug-report page from https://www.figma.com/make/1oP0cLPRq544kb13QSvPPM/Make-Template--Copy-?p=f&t=SXPjXXTcZTlDpvuJ-0&preview-route=%2Fbug-report in this project"

**Actions:**

1. Parse URL to extract fileKey=`1oP0cLPRq544kb13QSvPPM`
2. Run `get_design_context(fileKey="1oP0cLPRq544kb13QSvPPM", nodeId="")`
3. Locate the `/bug-report` page in the Make codebase
4. Read and understand the code for the `/bug-report` page, including its layout, components, and styling
5. Read and understand the project's structure, design system, and existing components
6. Create a new page component for the `/bug-report` page in the project using the project's conventions, especially the design system and existing components
7. If the project uses routing, create a new route for the bug report page
8. If the project has a navigation component, create a link to the new page

**Result:** Complete page matching Figma Make, integrated with project design system.

### Example 2: Implementing a single component

User says: "Implement the KPI component from the homepage of https://www.figma.com/make/9mKaqMoJCNMzN85GRkSL8K/Sales-Pipeline-Dashboard?p=f&t=4ZIjMVsCfHUW90gT-0 in this project"

**Actions:**

1. Parse URL to extract fileKey=`9mKaqMoJCNMzN85GRkSL8K`
2. Run `get_design_context(fileKey="9mKaqMoJCNMzN85GRkSL8K", nodeId="")`
3. Locate the KPI component in the Make codebase
4. Read and understand the code for the KPI component, including its layout, components, and styling
5. Read and understand the project's structure, design system, and existing components
6. Create a new component for the KPI in the project using the project's conventions, especially the design system and existing components. If a similar component already exists in the project, reuse it and customize it to match the Figma design instead of creating a new one from scratch.
7. If there are similar parts of the project that could be refactored to use the new KPI component, consider doing so. If this would result in significant changes to the look and feel of the project, ask the user for confirmation before proceeding.

**Result:** KPI component matching Figma Make, using the project design system and used consistently across the project.

### Example 3: Implementing an entire prototype consisting of multiple screens

User says: "Implement the entire prototype from https://www.figma.com/make/9mKaqMoJCNMzN85GRkSL8K/Sales-Pipeline-Dashboard?p=f&t=4ZIjMVsCfHUW90gT-0"

**Actions:**

1. Parse URL to extract fileKey=`9mKaqMoJCNMzN85GRkSL8K`
2. Run `get_design_context(fileKey="9mKaqMoJCNMzN85GRkSL8K", nodeId="")`
3. Read the entire prototype codebase to understand the overall structure, pages, navigation and components
4. Formulate a plan to implement the entire prototype, including the order of implementing pages and components, and how to ensure consistency across the implementation
5. Read and understand the current project's structure, design system, and existing components
6. If the current project already includes a UI that goes beyond simple boilerplate content, ask the user if they are ok with replacing the existing UI. If not, ask the user how to proceed, e.g., if the implementation should be done in a separate branch or if the existing UI should be kept and the new implementation should be added alongside it.
7. Update the implementation plan to ensure that the entire prototype will be implemented using the project's design system and existing components as much as possible, while still maintaining visual fidelity to the Figma design
8. Implement the prototype page by page and component by component, following the implementation plan and ensuring consistency with the project's design system and existing components. Validate frequently during implementation to catch any issues early.
9. Verify that all pages and components from the Figma prototype are implemented and that navigation works as in the prototype.

**Result:** Complete project matching the Figma Make prototype, including all pages, components and functionalities, using the project design system.

## Best Practices

### Always Start with Context

Never implement based on assumptions. Always fetch `get_design_context` first.

### Incremental Validation

Validate frequently during implementation, not just at the end. This catches issues early.

### Document Deviations

If you must deviate from the Figma design (e.g., for accessibility or technical constraints), document why in code comments.

### Reuse Over Recreation

Always check for existing components before creating new ones. Consistency across the codebase is more important than exact Figma replication.

### Design System First

When in doubt, prefer the project's design system patterns over literal Figma translation.

## Common Issues and Solutions

### Issue: Assets not loading

**Cause:** The Figma MCP server's assets endpoint is not accessible or the URLs are being modified.
**Solution:** Verify the Figma MCP server's assets endpoint is accessible. The server serves assets at `localhost` URLs. Use these directly without modification.

### Issue: Design token values differ from Figma

**Cause:** The project's design system tokens have different values than those specified in the Figma design.
**Solution:** When project tokens differ from Figma values, prefer project tokens for consistency but adjust spacing/sizing to maintain visual fidelity.
