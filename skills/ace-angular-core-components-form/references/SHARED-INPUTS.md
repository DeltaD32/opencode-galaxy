# Shared Inputs — `AlInputComponent`

Components that extend `AlInputComponent` share these inputs. Exceptions are noted per component.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Label text (appends `*` when `isRequired` is `true`) |
| `placeholder` | `string` | — | Placeholder text |
| `isRequired` | `boolean` | `false` | Required indicator + native `required` attribute |
| `isReadonly` | `boolean` | `false` | Readonly mode |
| `showErrors` | `boolean` | `false` | Shows native `validationMessage` when invalid and touched |
| `disabled` | `boolean` | `false` | Disabled state |
| `name` | `string` | — | Native `name` attribute (omit when using `formControlName`) |
| `value` | `T` | — | Programmatic value (prefer `formControlName`) |
| `tabIndex` | `number` | — | Tab index |

Bind via `formControlName` (preferred) or `[formControl]`. Do **not** set `name` when using `formControlName`.

---

## Prefix & Postfix (al-ds-input, al-ds-input-number only)

Use `<ng-template #prefix>` and `<ng-template #postfix>` inside the component for icons or text.

```html
<al-ds-input
  formControlName="price"
  label="Price">
  <ng-template #prefix>€</ng-template>
  <ng-template #postfix>.00</ng-template>
</al-ds-input>
```

```html
<al-ds-input-number
  formControlName="distance"
  label="Distance"
  [min]="0"
  [max]="999999">
  <ng-template #postfix>km</ng-template>
</al-ds-input-number>
```
