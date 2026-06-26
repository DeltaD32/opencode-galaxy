# Core-Components — Detailed Component Reference

Extended documentation for complex components that need more than a quick-reference entry.

---

## Dialog — `[alDialog]`

The dialog component is an attribute directive applied to a native `<dialog>` element. It provides modal and modeless dialog behavior with built-in header, content, footer slots, and cancel/confirm buttons.

### Setup

```typescript
import { AlDialogModule } from '@alphabet/core-components';

@Component({
  imports: [AlDialogModule],
})
```

### Template Structure

```html
<dialog alDialog #dialogRef="alDialog"
  title="Dialog Title"
  [hideConfirmButton]="false"
  confirmButtonLabel="Save"
  cancelButtonLabel="Cancel"
  (cancel)="onClose($event)">

  <div header>
    <!-- Optional custom header content -->
  </div>

  <div content>
    <!-- Main dialog body -->
  </div>

  <div footer>
    <!-- Optional custom footer content -->
  </div>
</dialog>
```

### Opening & Closing

Access via `viewChild`:

```typescript
readonly dialog = viewChild.required<AlDialogComponent>('dialogRef');
```

Three ways to open:

| Method | Description |
|---|---|
| `dialog.showModal(params?)` | Opens as modal (blocks background interaction) |
| `dialog.show(params?)` | Opens as modeless (background remains interactive) |
| `dialog.open(params?): Observable<string>` | Opens as modal, returns Observable that emits on close |

Close with `dialog.close(result?)`. The `cancel` output emits a `DialogResolution`.

### Passing & Accessing Params

```typescript
// Open with params
this.dialog().showModal({ vehicleId: '123' });

// Access inside the dialog's component
const id = this.dialog().param<string>('vehicleId');
```

### Fullscreen Mode

Set `[fullScreenOption]="true"` to show a fullscreen toggle button. Toggled via `dialog().changeFullSceen()`.

---

## Aside Panel — `al-ds-aside-wrapper`

A slide-in side panel for filters, detail views, or configuration. Opens from the right side of the viewport.

### Setup

```typescript
import { AsideWrapperComponent } from '@alphabet/core-components';

@Component({
  imports: [AsideWrapperComponent], // standalone
})
```

### Template

```html
<al-ds-aside-wrapper
  asideId="my-aside"
  title="Panel Title"
  [(isOpen)]="isPanelOpen"
  confirm="Apply"
  cancel="Cancel"
  (result)="onResult($event)">

  <!-- Option 1: Direct content -->
  <p>Panel content here</p>

  <!-- Option 2: Template ref -->
  <ng-template #templateRef>
    <app-filter-form />
  </ng-template>
</al-ds-aside-wrapper>
```

### Dynamic Component Rendering

Pass a component class via `[component]` and data via `[payload]`:

```html
<al-ds-aside-wrapper
  asideId="dynamic-aside"
  title="Vehicle Details"
  [(isOpen)]="isOpen"
  [component]="VehicleDetailComponent"
  [payload]="selectedVehicle"
  (result)="onDetailResult($event)" />
```

### Two-way Binding

`isOpen` uses Angular's `model()` signal — bind with `[(isOpen)]` for automatic open/close sync.

---

## Tabs — `al-ds-tabs`

### Setup

```typescript
import { AlTabsModule } from '@alphabet/core-components';

@Component({
  imports: [AlTabsModule],
})
```

### Tab Directive Config

Each tab is defined as an `<ng-template>` with the `[al-ds-tab]` directive:

```typescript
interface TabConfig {
  label: string;          // Required — tab label
  disabled?: boolean;     // Disable the tab
  notifications?: number; // Badge count
  prefix?: TemplateRef;   // Template before label
  postfix?: TemplateRef;  // Template after label
}
```

### Button Tabs

Button tabs trigger an action instead of showing content:

```typescript
interface ButtonTabConfig {
  label: string;          // Required — button label
  disabled?: boolean;     // Disable the button
  click: () => void;      // Required — click handler
}
```

### Lazy Loading

When `[lazyLoading]="true"`, tab content templates are only instantiated when the tab is first selected, reducing initial render cost.

### Auto-open

Use `auto-open="tabId"` to automatically select a specific tab on load.

---

## Attention Card — `al-ds-attention-card`

### Setup

```typescript
import { AlAttentionCardModule } from '@alphabet/core-components';

@Component({
  imports: [AlAttentionCardModule],
})
```

### Required Attributes

The component requires an `id` host attribute. The `icon` attribute is optional:

```html
<al-ds-attention-card id="unique-id" icon="warning" title="Warning Title">
  Body content
</al-ds-attention-card>
```

### Action Buttons

Use `AlAttentionCardButtonsDirective` to project action buttons:

```html
<al-ds-attention-card id="confirm-action" icon="info" title="Confirm">
  <p>Are you sure?</p>
  <ng-template alAttentionCardButtons>
    <al-ds-button label="Yes" type="primary" (clickEvent)="confirm()" />
    <al-ds-button label="No" type="outlined" (clickEvent)="cancel()" />
  </ng-template>
</al-ds-attention-card>
```

---

## Matrix — `al-matrix`

A pivot-table style grid that displays data organized by row and column attributes.

### Setup

```typescript
import { AlMatrixModule } from '@alphabet/core-components';

@Component({
  imports: [AlMatrixModule],
})
```

### Data Structure

The `values` array contains flat objects. The component pivots them using `rowAttr`, `columnAttr`, and `valueAttr`:

```typescript
matrixData = [
  { month: 'Jan', category: 'Fuel', amount: 150 },
  { month: 'Jan', category: 'Maintenance', amount: 80 },
  { month: 'Feb', category: 'Fuel', amount: 160 },
  { month: 'Feb', category: 'Maintenance', amount: 0 },
];
```

```html
<al-matrix
  [values]="matrixData"
  columnAttr="month"
  columnLabel="Month"
  rowAttr="category"
  rowLabel="Cost Type"
  valueAttr="amount"
  title="Monthly Vehicle Costs" />
```

### Interactive Mode

Set `[shouldBeSelector]="true"` to make cells selectable (emits `(change)` on selection).

Set `[shouldBeSwitched]="true"` to transpose rows and columns.

---

## Pagination — `al-ds-pagination`

### Setup

```typescript
import { AlPaginationModule } from '@alphabet/core-components';

@Component({
  imports: [AlPaginationModule],
})
```

### Configuration

Pagination is configured imperatively via `registerPaginator()`, not via inputs:

```typescript
readonly pagination = viewChild.required(AlPaginationComponent);

ngAfterViewInit(): void {
  this.pagination().registerPaginator({
    pageSize: 25,
    totalElements: this.totalItems,
    currentPage: 0,
    onPageChange: (page: number) => this.loadPage(page),
  });
}
```

Update after data changes:

```typescript
onDataLoaded(total: number): void {
  this.pagination().registerPaginator({
    ...this.paginatorConfig,
    totalElements: total,
  });
}
```
