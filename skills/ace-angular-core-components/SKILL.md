---
name: ace-angular-core-components
description: Angular @alphabet/core-components UI components for layouts, navigation, feedback, overlays, and data display. Excludes form inputs.
metadata:
  version: '1.0.0'
  authors:
  - name: Youri Mulder
    email: youri.mulder@bmwgroup.com
  tags:
  - angular
  - frontend
  - ui-components
  - core-components
---

# Core-Components — UI Components

Non-form UI components from `@alphabet/core-components`. For form inputs (al-ds-input, al-ds-dropdown, al-ds-checkbox, etc.), see the **ace-angular-core-components-form** skill.

See [EXAMPLES.md](EXAMPLES.md) for code examples. See [references/COMPONENTS.md](references/COMPONENTS.md) for detailed docs on complex components.

## Quick Reference

| Selector | Class | Import | Standalone? | Category |
|---|---|---|---|---|
| `al-ds-button` | `AlButtonComponent` | `AlButtonModule` | No | Action |
| `al-ds-action-menu` | `AlActionMenuComponent` | `AlActionMenuComponent` | Yes | Action |
| `al-ds-image-button` | `AlImageButtonComponent` | `AlImageButtonModule` | No | Action |
| `al-ds-card` | `AlCardComponent` | `AlCardModule` | No | Layout |
| `al-ds-listing-page` | `AlListingPageComponent` | `AlListingPageModule` | No | Layout |
| `al-ds-sub-header` | `AlSubHeaderComponent` | `AlSubHeaderModule` | No | Layout |
| `al-ds-title` | `AlTitleComponent` | `AlTitleModule` | No | Layout |
| `al-ds-footer` | `AlFooterComponent` | `AlFooterModule` | No | Layout |
| `al-ds-sidebar-navigation` | `AlSidebarContainerComponent` | `AlSidebarNavigationModule` | No | Layout |
| `al-ds-app-root` | `AlApplicationPageComponent` | `AlApplicationModule` | No | Layout |
| `al-ds-tabs` | `AlTabsComponent` | `AlTabsModule` | No | Navigation |
| `al-ds-steps` | `StepsComponent` | `StepsComponent` | Yes | Navigation |
| `al-ds-pagination` | `AlPaginationComponent` | `AlPaginationModule` | No | Navigation |
| `al-ds-scroll-to-top` | `AlScrollToTopComponent` | `AlScrollToTopComponent` | Yes | Navigation |
| `al-ds-dropdown-button-list` | `AlNavigationButtonListComponent` | `AlNavigationButtonModule` | No | Navigation |
| `al-ds-loading` | `AlLoadingComponent` | `AlLoadingComponent` | Yes | Feedback |
| `al-ds-progress-indicator` | `AlProgressIndicatorComponent` | `AlProgressIndicatorModule` | No | Feedback |
| `al-ds-status` | `AlStatusComponent` | `AlStatusModule` | No | Feedback |
| `al-ds-attention-card` | `AlAttentionCardComponent` | `AlAttentionCardModule` | No | Feedback |
| `al-ds-message` | `AlMessageComponent` | `AlNotificationsModule` | No | Feedback |
| `[alDialog]` | `AlDialogComponent` | `AlDialogModule` | No | Overlay |
| `al-ds-aside-wrapper` | `AsideWrapperComponent` | `AsideWrapperComponent` | Yes | Overlay |
| `al-ds-popover-content` | `AlPopoverComponent` | `AlPopoverModule` | No | Overlay |
| `[al-ds-tooltip]` | `AlTooltipDirective` | `AlTooltipModule` | No | Overlay |
| `al-ds-output` | `AlOutputComponent` | `AlOutputComponent` | Yes | Data Display |
| `al-ds-image` | `AlImageComponent` | `AlImageComponent` | Yes | Data Display |
| `al-ds-accordion` | `AlAccordionComponent` | `AlAccordionModule` | No | Data Display |
| `al-matrix` | `AlMatrixComponent` | `AlMatrixModule` | No | Data Display |
| `al-memo` | `AlMemoComponent` | `AlMemoModule` | No | Data Display |
| `al-diagnostics-panel` | `AlDiagnosticsPanelComponent` | `AlDiagnosticsModule` | No | Utility |

All imports come from `@alphabet/core-components`.

---

## Actions

### Button — `al-ds-button`

**Import:** `AlButtonModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Button label text |
| `type` | `AlButtonComponentType` | `'outlined'` | `'outlined'` \| `'primary'` \| `'ghost'` \| `'danger'` |
| `icon` | `string` | — | Icon name |
| `iconOnly` | `boolean` | `true` | Show icon without label |
| `disabled` | `boolean` | `false` | Disabled state |
| `loading` | `boolean` | `false` | Shows loading spinner |
| `element` | `AlButtonElement` | `'button'` | `'button'` \| `'a'` (renders as link) |
| `dropdown` | `boolean` | `false` | Show dropdown chevron |
| `options` | `NavigationOptionsModel[]` | `[]` | Dropdown menu options |
| `square` | `boolean` | `false` | Square shape |
| `autofocus` | `boolean` | `false` | Auto-focus on render |
| `tabIndex` | `number` | — | Tab index |

| Output | Type | Description |
|---|---|---|
| `clickEvent` | `Event` | Click event (use instead of native `(click)`) |

Uses `<ng-content>` for custom inner content.

⚠️ **Form submit:** `al-ds-button` renders an internal `<button>` that can trigger the form's `(ngSubmit)`. Choose **one** submit mechanism — either `(ngSubmit)` on the `<form>` **or** `(clickEvent)` on the button — never both, or the handler fires twice.

### Action Menu — `al-ds-action-menu`

**Import:** `AlActionMenuComponent` (standalone)

| Input | Type | Default | Description |
|---|---|---|---|
| `dropdownOptions` | `NavigationOptionsModel[]` | `[]` | Menu items |

### Image Button — `al-ds-image-button`

**Import:** `AlImageButtonModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `src` | `string` | — | Image source URL |
| `alt` | `string` | — | Alt text |
| `disabled` | `boolean` | `false` | Disabled state |

| Output | Type | Description |
|---|---|---|
| `click` | `Event` | Click event |

---

## Layout

### Card — `al-ds-card`

**Import:** `AlCardModule` · No inputs. Content-projection only wrapper.

### Title — `al-ds-title`

**Import:** `AlTitleModule`

| Input | Type | Description |
|---|---|---|
| `label` | `string` | Page title text |

### Sub Header — `al-ds-sub-header`

**Import:** `AlSubHeaderModule`

| Input | Type | Description |
|---|---|---|
| `label` | `string` | Sub-header text |

### Listing Page — `al-ds-listing-page`

**Import:** `AlListingPageModule`

| Input | Type | Description |
|---|---|---|
| `moreResults` | `boolean` | Whether more results are available |

| Output | Type | Description |
|---|---|---|
| `showMore` | `void` | Emitted when "show more" is clicked |

### Footer — `al-ds-footer`

**Import:** `AlFooterModule` · No inputs.

### Sidebar Navigation — `al-ds-sidebar-navigation`

**Import:** `AlSidebarNavigationModule` · No inputs. Uses content projection for navigation items.

### Application Root — `al-ds-app-root`

**Import:** `AlApplicationModule` · Top-level layout shell. Contains header, sidebar, and content areas.

---

## Navigation

### Tabs — `al-ds-tabs`

**Import:** `AlTabsModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `auto-open` | `string` | — | ID of tab to auto-open |
| `lazyLoading` | `boolean` | `false` | Lazy-load tab content |

| Output | Type | Description |
|---|---|---|
| `selectedTabEvent` | `number` | Emitted with tab index on selection |
| `onChange` | `AlTabDirective` | Emitted with the selected tab directive |

Tabs are defined using directives on `<ng-template>`:
- `[al-ds-tab]` — content tab with config: `{ label: string; disabled?: boolean; notifications?: number; prefix?: TemplateRef; postfix?: TemplateRef }`
- `[al-ds-button-tab]` — action tab with config: `{ label: string; disabled?: boolean; click: () => void }`

See [references/COMPONENTS.md](references/COMPONENTS.md) for detailed usage.

### Steps — `al-ds-steps`

**Import:** `StepsComponent` (standalone)

| Input | Type | Default | Description |
|---|---|---|---|
| `stepRoutes` | `StepRoute[]` | — | Step configuration array |
| `resetValidationOnFirstStep` | `boolean` | `true` | Reset validation when returning to first step |

| Output | Type | Description |
|---|---|---|
| `navigate` | `StepNavigateEvent` | Emitted on step navigation |

### Pagination — `al-ds-pagination`

**Import:** `AlPaginationModule` · Configured via `registerPaginator(paginator: AlPaginationHandlerModel)` method, not inputs.

### Scroll to Top — `al-ds-scroll-to-top`

**Import:** `AlScrollToTopComponent` (standalone) · No inputs. Renders a floating button that scrolls to the page top.

### Navigation Button List — `al-ds-dropdown-button-list`

**Import:** `AlNavigationButtonModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `options` | `NavigationOptionsModel[]` | — | Button options |
| `params` | `Record<string, any>` | `{}` | Route params |

---

## Feedback

### Loading — `al-ds-loading`

**Import:** `AlLoadingComponent` (standalone)

| Input | Type | Default | Description |
|---|---|---|---|
| `isLoading` | `boolean \| null` | `null` | Shows loading spinner when `true` |

### Progress Indicator — `al-ds-progress-indicator`

**Import:** `AlProgressIndicatorModule` · No inputs. Driven internally.

### Status — `al-ds-status`

**Import:** `AlStatusModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `status` | `AlStatusState` | `'DEFAULT'` | Status state: `'DEFAULT'` \| `'WARNING'` \| `'ERROR'` \| `'SUCCESS'` |

Uses `<ng-content>` for status text.

### Attention Card — `al-ds-attention-card`

**Import:** `AlAttentionCardModule`

| Input | Type | Default | Required | Description |
|---|---|---|---|---|
| `id` | `string` | — | Yes | Unique identifier (host attribute) |
| `title` | `string` | — | No | Card title |
| `subtitle` | `string` | — | No | Card subtitle |
| `icon` | `string` | — | No | Icon name (host attribute) |
| `status` | `'error' \| undefined` | — | No | Error styling when `'error'` |
| `isCollapsible` | `boolean` | `false` | No | Collapsible card |

| Output | Type | Description |
|---|---|---|
| `onClose` | `any` | Close button clicked |

Uses `<ng-content>` for body. Supports `AlAttentionCardButtonsDirective` for action buttons.

### Message / Notification — `al-ds-message`

**Import:** `AlNotificationsModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `type` | `AlMessageType \| null` | `null` | `'info'` \| `'success'` \| `'warning'` \| `'error'` |
| `message` | `string` | — | Message text (two-way via `model()`) |

---

## Overlays

### Dialog — `[alDialog]`

**Import:** `AlDialogModule` · Attribute directive on a `<dialog>` element.

| Input | Type | Default | Description |
|---|---|---|---|
| `title` | `string` | — | Dialog title |
| `hideCancelButton` | `boolean` | `false` | Hide cancel button |
| `hideConfirmButton` | `boolean` | `true` | Hide confirm button |
| `disableConfirmButton` | `boolean` | `false` | Disable confirm button |
| `cancelButtonLabel` | `string` | `'cancel'` | Cancel button label |
| `confirmButtonLabel` | `string` | `'confirm'` | Confirm button label |
| `fullScreenOption` | `boolean` | `false` | Show fullscreen toggle |
| `disableScroll` | `boolean` | `false` | Disable body scroll |

| Output | Type | Description |
|---|---|---|
| `cancel` | `DialogResolution` | Emitted on close |

Open via `viewChild`: `dialogRef().showModal()`, `dialogRef().show()`, or `dialogRef().open()` (returns `Observable`). Close via `dialogRef().close()`.

Content slots: `[header]`, `[content]`, `[footer]`.

See [references/COMPONENTS.md](references/COMPONENTS.md) for detailed usage.

### Aside Panel — `al-ds-aside-wrapper`

**Import:** `AsideWrapperComponent` (standalone)

| Input | Type | Default | Description |
|---|---|---|---|
| `asideId` | `string` | — | **(Required)** Unique ID |
| `title` | `string` | — | **(Required)** Panel title |
| `isOpen` | `boolean` | `false` | Two-way binding (`model()`) |
| `confirm` | `string` | `'apply'` | Confirm button label |
| `cancel` | `string` | `'cancel'` | Cancel button label |
| `component` | `any` | — | Dynamic component to render |
| `payload` | `any` | — | Data payload |

| Output | Type | Description |
|---|---|---|
| `result` | `any` | Emitted on aside close |

Uses `<ng-content>` or `#templateRef` for content.

### Tooltip — `[al-ds-tooltip]`

**Import:** `AlTooltipModule` · Attribute directive.

| Input | Type | Default | Description |
|---|---|---|---|
| `al-ds-tooltip` | `any` | — | Tooltip content |
| `truncate` | `boolean` | `false` | Truncate long text |
| `width` | `string` | — | Custom width |

### Popover — `al-ds-popover-content`

**Import:** `AlPopoverModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `content` | `string \| null` | `null` | Text content |
| `contentTemplate` | `TemplateRef \| null` | `null` | Template content |

---

## Data Display

### Output — `al-ds-output`

**Import:** `AlOutputComponent` (standalone)

Displays read-only label/value pairs. Use instead of disabled inputs for display-only data.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | `''` | Label text |
| `value` | `string` | `''` | Display value |
| `placeHolder` | `string` | `'Placeholder'` | Placeholder when empty |
| `renderAsOutput` | `boolean` | `false` | Output styling |
| `inputTemplate` | `TemplateRef \| null` | `null` | Custom value template |

### Image — `al-ds-image`

**Import:** `AlImageComponent` (standalone)

| Input | Type | Default | Description |
|---|---|---|---|
| `imageUrl` | `string \| null` | — | Image source |
| `noImageUrl` | `string` | `'assets/no-image.png'` | Fallback image |
| `width` | `string` | — | CSS width |
| `height` | `string` | — | CSS height |
| `alt` | `string` | — | Alt text |

### Accordion — `al-ds-accordion`

**Import:** `AlAccordionModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Accordion header label |
| `disabled` | `boolean` | `false` | Disabled state |
| `showBody` | `boolean` | `false` | Expanded state (two-way via `model()`) |

| Output | Type | Description |
|---|---|---|
| `expandChanged` | `boolean` | Emitted on expand/collapse |

Content slots: `[headerOutlet]` for custom header, default `<ng-content>` for body.

### Matrix — `al-matrix`

**Import:** `AlMatrixModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `values` | `any[]` | `[]` | Data array |
| `columnAttr` | `string` | — | Property name for columns |
| `columnLabel` | `string` | — | Column header label |
| `rowAttr` | `string` | — | Property name for rows |
| `rowLabel` | `string` | — | Row header label |
| `valueAttr` | `string` | — | Property name for cell values |
| `title` | `string` | — | Matrix title |
| `shouldBeSwitched` | `boolean` | `false` | Transpose rows/columns |
| `shouldBeSelector` | `boolean` | `false` | Render cells as selectable |
| `defaultInput` | `boolean` | `false` | Show default input |
| `toggle` | `string` | — | Toggle label |

| Output | Type | Description |
|---|---|---|
| `change` | `any` | Cell value changed |
| `defaultChange` | `boolean` | Default toggle changed |

### Memo — `al-memo`

**Import:** `AlMemoModule`

| Input | Type | Default | Description |
|---|---|---|---|
| `dateFormat` | `string` | `'dd-MM-yyyy'` | Date display format |
| `maxNotificationMemos` | `number` | `9` | Max notification badge count |
| `range` | `number` | `5` | Items per page |

---

## Utility

### Diagnostics Panel — `al-diagnostics-panel`

**Import:** `AlDiagnosticsModule` · Dev-only panel showing environment and build info. No inputs.
