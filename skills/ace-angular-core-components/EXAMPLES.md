# Core-Components UI — Code Examples

All imports come from `@alphabet/core-components`.

---

## Button

### Primary button

```html
<al-ds-button label="Save" type="primary" (clickEvent)="onSave()" />
```

### Icon-only button

```html
<al-ds-button icon="edit" [iconOnly]="true" type="ghost" (clickEvent)="onEdit()" />
```

### Button with loading state

```html
<al-ds-button label="Submit" type="primary" [loading]="isSubmitting" [disabled]="isSubmitting" (clickEvent)="onSubmit()" />
```

### Button with dropdown menu

```html
<al-ds-button label="Actions" [dropdown]="true" [options]="actionOptions" type="outlined" />
```

## Action Menu

```html
<al-ds-action-menu [dropdownOptions]="menuOptions" />
```

## Image Button

```html
<al-ds-image-button src="assets/logo.svg" alt="Company Logo" (click)="onLogoClick()" />
```

---

## Card

```html
<al-ds-card>
  <h3>Card Title</h3>
  <p>Card content goes here.</p>
</al-ds-card>
```

## Title

```html
<al-ds-title label="Vehicle Overview" />
```

## Sub Header

```html
<al-ds-sub-header label="Registration Details" />
```

## Listing Page

```html
<al-ds-listing-page [moreResults]="hasMore" (showMore)="loadMore()">
  @for (item of items; track $index) {
    <div>{{ item.name }}</div>
  }
</al-ds-listing-page>
```

## Footer

```html
<al-ds-footer />
```

## Scroll to Top

```html
<al-ds-scroll-to-top />
```

---

## Tabs

### Basic tabs

```html
<al-ds-tabs (selectedTabEvent)="onTabChange($event)">
  <ng-template [al-ds-tab]="{ label: 'General' }">
    <p>General content</p>
  </ng-template>
  <ng-template [al-ds-tab]="{ label: 'Details', notifications: 3 }">
    <p>Details content with notification badge</p>
  </ng-template>
  <ng-template [al-ds-tab]="{ label: 'Disabled', disabled: true }">
    <p>This tab is disabled</p>
  </ng-template>
</al-ds-tabs>
```

### Tabs with lazy loading

```html
<al-ds-tabs [lazyLoading]="true">
  <ng-template [al-ds-tab]="{ label: 'Heavy Content' }">
    <app-expensive-component />
  </ng-template>
</al-ds-tabs>
```

### Button tab (action, not content)

```html
<al-ds-tabs>
  <ng-template [al-ds-tab]="{ label: 'Content Tab' }">
    <p>Some content</p>
  </ng-template>
  <ng-template [al-ds-button-tab]="{ label: 'Export', click: onExport }"></ng-template>
</al-ds-tabs>
```

## Steps

```html
<al-ds-steps [stepRoutes]="steps" (navigate)="onStepNavigate($event)" />
```

```typescript
steps: StepRoute[] = [
  { label: 'Vehicle Info', route: 'vehicle-info', valid: true },
  { label: 'Registration', route: 'registration', valid: false },
  { label: 'Review', route: 'review', valid: false },
];
```

## Pagination

```typescript
readonly pagination = viewChild.required(AlPaginationComponent);

ngAfterViewInit() {
  this.pagination().registerPaginator({
    pageSize: 25,
    totalElements: 250,
    currentPage: 0,
    onPageChange: (page) => this.loadPage(page),
  });
}
```

```html
<al-ds-pagination />
```

## Navigation Button List

```html
<al-ds-dropdown-button-list [options]="navOptions" [params]="{ id: vehicleId }" />
```

---

## Loading

```html
<al-ds-loading [isLoading]="isLoading()">
  <p>Content shown when not loading</p>
</al-ds-loading>
```

## Status

```html
<al-ds-status status="SUCCESS">Active</al-ds-status>
<al-ds-status status="WARNING">Pending Review</al-ds-status>
<al-ds-status status="ERROR">Rejected</al-ds-status>
<al-ds-status>Default</al-ds-status>
```

## Attention Card

```html
<al-ds-attention-card
  id="missing-vin"
  icon="warning"
  title="Missing VIN"
  subtitle="Vehicle identification number is required"
  (onClose)="dismissWarning()">
  <p>Please enter the 17-character VIN to proceed.</p>
</al-ds-attention-card>
```

### Collapsible with error status

```html
<al-ds-attention-card
  id="validation-errors"
  icon="error"
  title="Validation Errors"
  status="error"
  [isCollapsible]="true">
  <ul>
    <li>Registration plate is required</li>
    <li>CO₂ emission must be between 0 and 500</li>
  </ul>
</al-ds-attention-card>
```

## Message / Notification

```html
<al-ds-message type="success" [message]="successMessage" />
<al-ds-message type="error" [message]="errorMessage" />
<al-ds-message type="warning" [message]="warningMessage" />
<al-ds-message type="info" [message]="infoMessage" />
```

---

## Dialog

### Template

```html
<dialog alDialog #myDialog="alDialog"
  title="Confirm Deletion"
  [hideConfirmButton]="false"
  confirmButtonLabel="Delete"
  (cancel)="onDialogClose($event)">
  <div content>
    <p>Are you sure you want to delete this vehicle?</p>
  </div>
</dialog>
```

### Opening from component

```typescript
readonly dialog = viewChild.required<AlDialogComponent>('myDialog');

openConfirmation(): void {
  this.dialog().showModal();
}

// Or with observable result:
openAndWait(): void {
  this.dialog().open().subscribe((result) => {
    if (result === 'confirm') {
      this.deleteVehicle();
    }
  });
}
```

### Passing params

```typescript
this.dialog().showModal({ vehicleId: '123', vehicleName: 'BMW 320i' });

// Access in dialog template via dialog ref:
// this.dialog().param<string>('vehicleId')
```

## Aside Panel

```html
<al-ds-aside-wrapper
  asideId="vehicle-filter"
  title="Filter Vehicles"
  [(isOpen)]="isFilterOpen"
  confirm="Apply Filters"
  cancel="Reset"
  (result)="onFilterResult($event)">
  <ng-template #templateRef>
    <app-vehicle-filter [payload]="filterPayload" />
  </ng-template>
</al-ds-aside-wrapper>
```

## Tooltip

```html
<span [al-ds-tooltip]="'VIN: Vehicle Identification Number'">VIN</span>

<!-- With truncation -->
<span [al-ds-tooltip]="longDescription" [truncate]="true" width="300px">{{ longDescription }}</span>
```

## Popover

```html
<al-ds-popover-content content="Simple text popover" />

<!-- With template -->
<al-ds-popover-content [contentTemplate]="popoverTpl">
  <ng-template #popoverTpl>
    <h4>Custom content</h4>
    <p>Rich popover content here</p>
  </ng-template>
</al-ds-popover-content>
```

---

## Output

```html
<al-ds-output label="Registration Plate" value="AB-123-CD" [renderAsOutput]="true" />
```

### With custom template

```html
<al-ds-output label="Status" [inputTemplate]="statusTpl">
    <ng-template #statusTpl>
        <al-ds-status status="SUCCESS">Active</al-ds-status>
    </ng-template>
</al-ds-output>
```

## Image

```html
<al-ds-image [imageUrl]="vehicle.photoUrl" alt="Vehicle Photo" width="200px" height="150px" />
```

## Accordion

```html
<al-ds-accordion label="Technical Specifications" [(showBody)]="isTechOpen">
    <p>Engine: 2.0L Turbo</p>
    <p>Power: 190 hp</p>
</al-ds-accordion>
```

### With custom header

```html
<al-ds-accordion [(showBody)]="isOpen">
    <div headerOutlet>
        <strong>Custom Header</strong>
        <al-ds-status status="WARNING">Draft</al-ds-status>
    </div>
    <p>Body content</p>
</al-ds-accordion>
```

## Matrix

```html
<al-matrix
        [values]="matrixData"
        columnAttr="month"
        columnLabel="Month"
        rowAttr="category"
        rowLabel="Category"
        valueAttr="amount"
        title="Monthly Costs"
        (change)="onMatrixChange($event)" />
```

## Memo

```html
<al-memo dateFormat="dd-MM-yyyy" [maxNotificationMemos]="5" [range]="10" />
```
