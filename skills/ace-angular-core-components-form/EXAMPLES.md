# Core-Components Form Examples

All imports come from `@alphabet/core-components`.

---

## Text Input — `al-ds-input`

```html
<al-ds-input
  formControlName="email"
  label="Email Address"
  type="email"
  placeholder="user@example.com"
  [isRequired]="true"
  [showErrors]="true" />
```

### With prefix/postfix

```html
<al-ds-input
  formControlName="price"
  label="Price">
  <ng-template #prefix>€</ng-template>
  <ng-template #postfix>.00</ng-template>
</al-ds-input>
```

## Textarea — `al-ds-textarea`

```html
<al-ds-textarea
  formControlName="description"
  label="Description"
  placeholder="Enter a description"
  [rows]="4"
  [isRequired]="true"
  [showErrors]="true" />
```

## Number Input — `al-ds-input-number`

```html
<al-ds-input-number
  formControlName="quantity"
  label="Quantity"
  [min]="1"
  [max]="100"
  [step]="1"
  [isRequired]="true"
  [showErrors]="true" />
```

### With prefix/postfix

```html
<al-ds-input-number
  formControlName="distance"
  label="Distance"
  [min]="0"
  [max]="999999">
  <ng-template #postfix>km</ng-template>
</al-ds-input-number>
```

## Date Input — `al-ds-input-date`

```html
<al-ds-input-date
  formControlName="startDate"
  label="Start Date"
  [isRequired]="true"
  [showErrors]="true" />
```

## Time Input — `al-ds-input-time`

### Time only

```html
<al-ds-input-time
  formControlName="startTime"
  label="Start Time"
  minTime="06:00"
  maxTime="23:59"
  [isRequired]="true"
  [showErrors]="true" />
```

### DateTime

```html
<al-ds-input-time
  formControlName="appointmentDateTime"
  label="Appointment"
  inputType="datetime-local"
  [isRequired]="true"
  [showErrors]="true" />
```

## File Upload — `al-ds-file-upload`

```html
<al-ds-file-upload
  formControlName="document"
  label="Upload Document"
  [accept]="['.pdf', '.docx']"
  [isRequired]="true" />
```

## From-Until Wrapper — `al-ds-from-until`

```html
<al-ds-from-until>
  <al-ds-input-time formControlName="startTime" label="From" minTime="06:00" [isRequired]="true" [showErrors]="true" />
  <al-ds-input-time formControlName="endTime" label="Until" maxTime="23:59" [isRequired]="true" [showErrors]="true" />
</al-ds-from-until>
```

## Range Slider — `al-ds-range`

```html
<al-ds-range
  formControlName="priceRange"
  [min]="0"
  [max]="1000"
  [step]="50"
  [numbered]="true"
  label="Price Range" />
```

## Range with Input — `al-ds-range-with-input`

```html
<al-ds-range-with-input
  formControlName="budgetRange"
  [min]="0"
  [max]="50000"
  [step]="500"
  unit="€"
  label="Budget Range" />
```

## Slider — `al-ds-slider`

```html
<al-ds-slider
  formControlName="volume"
  [min]="0"
  [max]="100"
  [step]="5"
  [numbered]="true"
  [numberInterval]="25"
  label="Volume" />
```

## Slider with Input — `al-ds-slider-with-input`

```html
<al-ds-slider-with-input
  formControlName="budget"
  [min]="0"
  [max]="10000"
  [step]="500"
  unit="€"
  label="Budget" />
```

## Dropdown — `al-ds-dropdown`

### Basic with object options

```html
<al-ds-dropdown
  formControlName="venueType"
  label="Venue Type"
  [isRequired]="true"
  [options]="venueTypeOptions"
  [template]="venueTypeTemplate">
  <ng-template #venueTypeTemplate let-value>{{ value.description }}</ng-template>
</al-ds-dropdown>
```

### Multi-select

```html
<al-ds-dropdown
  formControlName="brands"
  label="Brands"
  [options]="brandsOptions"
  [multiSelect]="true"
  [multiSelectPlaceholderCount]="true"
  placeholder="Select brands"
  [template]="brandsTemplate">
  <ng-template #brandsTemplate let-value>{{ value.description }}</ng-template>
</al-ds-dropdown>
```

> When using `template`, the component cannot be self-closed because it contains `<ng-template>` child content.

## Checkbox — `al-ds-checkbox`

### Standalone

```html
<al-ds-checkbox formControlName="agreeTerms" label="I agree to the terms" />
```

### Group with "Select All"

```html
<al-ds-checkbox
  [multiple]="'full'"
  formControlName="selectAll"
  label="Select All" />
<div formArrayName="options">
  @for (option of options.controls; track $index) {
    <al-ds-checkbox
      [multiple]="'set'"
      [formControlName]="$index"
      [label]="optionLabels[$index]" />
  }
</div>
```

### Lock directive

```html
<al-ds-checkbox formControlName="protected" label="Protected" lock [locked]="true" />
```

## Radio Button — `al-ds-radio`

```html
<fieldset>
  <legend>Gender *</legend>
  <al-ds-radio formControlName="gender" label="Male" value="male" />
  <al-ds-radio formControlName="gender" label="Female" value="female" />
  <al-ds-radio formControlName="gender" label="Non-binary" value="non-binary" />
</fieldset>
```

## Switch — `al-ds-switch`

```html
<al-ds-switch
  formControlName="isActive"
  label="Active"
  [showLabelAbove]="true" />
```

## Input Autocomplete — `al-ds-input[al-ds-autocomplete]`

### Basic autocomplete

```html
<al-ds-input
  formControlName="city"
  label="City"
  al-ds-autocomplete
  [options]="filteredCities"
  (search)="onCitySearch($event)"
  (select-option)="onCitySelect($event)" />
```

### With custom template

```html
<al-ds-input
  formControlName="vehicle"
  label="Vehicle"
  al-ds-autocomplete
  [options]="filteredVehicles"
  [template]="vehicleTpl"
  [debounceTime]="300"
  [enableFocus]="true"
  (search)="onVehicleSearch($event)"
  (select-option)="onVehicleSelect($event)">
  <ng-template #vehicleTpl let-option>
    <strong>{{ option.make }}</strong> — {{ option.model }} ({{ option.year }})
  </ng-template>
</al-ds-input>
```

---

## Submit Button — `al-ds-button`

### Form with ngSubmit

```html
<form [formGroup]="myForm" (ngSubmit)="onSubmit()">
  <al-ds-input
    formControlName="name"
    label="Name"
    [isRequired]="true"
    [showErrors]="true" />
  <al-ds-input
    formControlName="email"
    label="Email"
    type="email"
    [isRequired]="true"
    [showErrors]="true" />
  <al-ds-button
    label="Submit"
    type="primary"
    [disabled]="myForm.invalid" />
</form>
```

### Form with clickEvent (alternative)

```html
<form [formGroup]="myForm">
  <al-ds-input
    formControlName="name"
    label="Name"
    [isRequired]="true"
    [showErrors]="true" />
  <al-ds-button
    label="Submit"
    type="primary"
    [loading]="isSubmitting"
    [disabled]="myForm.invalid || isSubmitting"
    (clickEvent)="onSubmit()" />
</form>
```

---

## Directives

### Eager input

```html
<al-ds-input formControlName="search" label="Search" eager />
```

### No decimal

```html
<al-ds-input-number formControlName="quantity" label="Quantity" al-ds-no-decimal />
```

### Uppercase

```html
<al-ds-input formControlName="code" label="Code" uppercase />
```
