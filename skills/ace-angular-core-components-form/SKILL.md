---
name: ace-angular-core-components-form
description: Angular @alphabet/core-components form inputs for text, dropdowns, checkboxes, radios, file upload, sliders, and directives.
metadata:
  version: '1.0.0'
  authors:
  - name: Youri Mulder
    email: youri.mulder@bmwgroup.com
  tags:
  - angular
  - frontend
  - forms
  - ui-components
  - core-components
---

# Core-Components for Form Inputs

Replace native HTML form elements with `@alphabet/core-components` whenever the input type is supported.

See [EXAMPLES.md](EXAMPLES.md) for code examples of every component.

## Quick Reference

| HTML element / type | Core-component | Import | Standalone? |
|---|---|---|---|
| `<input type="text\|password\|tel\|email">` | `al-ds-input` | `AlInputModule` | No |
| `<textarea>` | `al-ds-textarea` | `AlInputModule` | No |
| `<input type="number">` | `al-ds-input-number` | `AlInputModule` | No |
| `<input type="date">` | `al-ds-input-date` | `AlInputDateComponent` | Yes |
| `<input type="time\|datetime-local">` | `al-ds-input-time` | `AlInputTimeComponent` | Yes |
| `<input type="file">` | `al-ds-file-upload` | `AlInputModule` | No |
| `<select>` | `al-ds-dropdown` | `AlDropdownComponent` | Yes |
| `<input type="checkbox">` | `al-ds-checkbox` | `AlSelectorModule` | No |
| `<input type="radio">` | `al-ds-radio` | `AlSelectorModule` | No |
| toggle / switch | `al-ds-switch` | `AlSwitchesModule` | No |
| dual-thumb range | `al-ds-range` | `AlRangeComponent` | Yes |
| dual-thumb range + inputs | `al-ds-range-with-input` | `AlRangeWithInputComponent` | Yes |
| single-thumb slider | `al-ds-slider` | `AlSliderComponent` | Yes |
| single-thumb slider + input | `al-ds-slider-with-input` | `AlSliderWithInputComponent` | Yes |
| autocomplete input | `al-ds-input[al-ds-autocomplete]` | `AlInputAutocompleteModule` | No |
| from-until wrapper | `al-ds-from-until` | `AlInputModule` | No |
| `<button type="submit">` | `al-ds-button` | `AlButtonModule` | No |

All imports come from `@alphabet/core-components`.

If an input type is not listed in the table above, use the native HTML element instead.

Use self-closing tags when the component has no child content.

---

## Shared Inputs (from `AlInputComponent`)

Components marked "Extends `AlInputComponent`" share common inputs. See [references/SHARED-INPUTS.md](references/SHARED-INPUTS.md) for the full table and details.

---

## Text Input — `al-ds-input`

**Import:** `AlInputModule` · **Extends** `AlInputComponent`

| Input | Type | Default | Description |
|---|---|---|---|
| `type` | `'text' \| 'password' \| 'tel' \| 'email'` | `'text'` | Input type |

All shared inputs apply.

---

## Textarea — `al-ds-textarea`

**Import:** `AlInputModule` · **Extends** `AlInputComponent`

| Input | Type | Default | Description |
|---|---|---|---|
| `rows` | `number` | `1` | Visible text rows |

All shared inputs apply.

---

## Number Input — `al-ds-input-number`

**Import:** `AlInputModule` · **Extends** `AlInputComponent`

| Input | Type | Default | Description |
|---|---|---|---|
| `min` | `number` | — | Minimum value |
| `max` | `number` | — | Maximum value |
| `step` | `number \| string` | `1` | Step increment |
| `hideControls` | `boolean` | `false` | Hides +/- stepper buttons |
| `startOnMin` | `boolean` | `true` | Starts from `min` value instead of 0 |

All shared inputs apply. Supports prefix/postfix.

---

## Date Input — `al-ds-input-date`

**Import:** `AlInputDateComponent` (standalone) · **Extends** `AlInputComponent`

Internally wraps `al-ds-input-time` with `inputType="date"`.

| Input | Type | Default | Description |
|---|---|---|---|
| `minDate` | `Date` | — | Earliest selectable date |
| `maxDate` | `Date` | — | Latest selectable date |

All shared inputs apply.

---

## Time / DateTime Input — `al-ds-input-time`

**Import:** `AlInputTimeComponent` (standalone) · **Extends** `AlInputComponent`

| Input | Type | Default | Description |
|---|---|---|---|
| `inputType` | `'time' \| 'date' \| 'datetime-local'` | `'time'` | Input mode |
| `minTime` | `string \| null` | `null` | Min time (`hh:mm`), time mode only |
| `maxTime` | `string \| null` | `null` | Max time (`hh:mm`), time mode only |
| `minDate` | `Date \| null` | `null` | Min date, date/datetime modes only |
| `maxDate` | `Date \| null` | `null` | Max date, date/datetime modes only |

⚠️ **`pickDateTime` is deprecated.** Use `inputType="datetime-local"` instead.

All shared inputs apply.

---

## File Upload — `al-ds-file-upload`

**Import:** `AlInputModule` · **Extends** `AlInputComponent`

| Input | Type | Default | Description |
|---|---|---|---|
| `accept` | `string[]` | `[]` | Accepted file types (e.g. `['.pdf', '.jpg']`) |

All shared inputs apply.

---

## From-Until Wrapper — `al-ds-from-until`

**Import:** `AlInputModule` · No inputs. Layout-only wrapper that inserts an arrow (`→`) between child elements. Typically wraps two date/time inputs.


---

## Range Slider — `al-ds-range`

**Import:** `AlRangeComponent` (standalone) · **Value type:** `number[]` (two-element array `[min, max]`)

⚠️ Does **not** extend `AlInputComponent`. Shared inputs do not apply.

| Input | Type | Default | Description |
|---|---|---|---|
| `min` | `number` | `0` | Range minimum |
| `max` | `number` | `100` | Range maximum |
| `step` | `number` | — | Snap increment |
| `label` | `string` | — | Label above slider |
| `numbered` | `boolean` | `false` | Show tick marks |
| `numberInterval` | `number \| null` | `null` | Tick interval (falls back to `step`) |
| `allowInversion` | `boolean` | `false` | Allow min thumb past max thumb |
| `disabled` | `boolean` | `false` | Disabled state |

---

## Range with Number Inputs — `al-ds-range-with-input`

**Import:** `AlRangeWithInputComponent` (standalone) · **Value type:** `RangeInput` (`{ firstValue: number; lastValue: number; values?: number[] }`)

⚠️ Does **not** extend `AlInputComponent`. Shared inputs do not apply.

| Input | Type | Default | Description |
|---|---|---|---|
| `min` | `number` | `0` | Minimum value |
| `max` | `number` | `100` | Maximum value |
| `step` | `number` | — | Step increment |
| `label` | `string` | — | Label above component |
| `unit` | `string` | — | Unit prefix in number inputs (e.g. `€`) |
| `disabled` | `boolean` | `false` | Disabled state |
| `range` | `RangeInput` | `{ firstValue: min, lastValue: max }` | Initial values |

Number inputs cross-validate: min cannot exceed max and vice versa.

---

## Slider — `al-ds-slider`

**Import:** `AlSliderComponent` (standalone) · **Value type:** `number`

⚠️ Does **not** extend `AlInputComponent`. Shared inputs do not apply.

| Input | Type | Default | Description |
|---|---|---|---|
| `min` | `number` | — | **(Required)** Minimum |
| `max` | `number` | — | **(Required)** Maximum |
| `step` | `number` | `1` | Step increment |
| `label` | `string` | — | Label above slider |
| `numbered` | `boolean` | `false` | Show tick marks |
| `numberInterval` | `number \| null` | `null` | Tick interval |
| `disabled` | `boolean` | `false` | Disabled state |

---

## Slider with Number Input — `al-ds-slider-with-input`

**Import:** `AlSliderWithInputComponent` (standalone) · **Value type:** `number`

⚠️ Does **not** extend `AlInputComponent`. Shared inputs do not apply.

| Input | Type | Default | Description |
|---|---|---|---|
| `min` | `number` | `0` | Minimum value |
| `max` | `number` | `100` | Maximum value |
| `step` | `number` | `10` | Step increment |
| `label` | `string` | — | Label above component |
| `unit` | `string` | — | Unit prefix (e.g. `€`) |
| `disabled` | `boolean` | `false` | Disabled state |

---

## Slider vs Range — When to use which?

| Need | Component |
|---|---|
| Single value | `al-ds-slider` |
| Single value + text input | `al-ds-slider-with-input` |
| Min/max pair (two thumbs) | `al-ds-range` |
| Min/max pair + text inputs | `al-ds-range-with-input` |

---

## Dropdown — `al-ds-dropdown`

**Import:** `AlDropdownComponent` (standalone) · Implements `ControlValueAccessor` directly.

⚠️ Does **not** extend `AlInputComponent`. **These shared inputs do NOT exist:** `name`, `isReadonly`, `showErrors`. Use `formControlName` for binding.

| Input | Type | Default | Description |
|---|---|---|---|
| `options` | `any[]` | `[]` | Strings or objects with `value`/`description` |
| `label` | `string` | — | Label (appends `*` when `isRequired` is `true`) |
| `placeholder` | `string` | `'Make a selection'` | Placeholder text |
| `isRequired` | `boolean` | `false` | Required `*` indicator |
| `multiSelect` | `boolean` | `false` | Multi-selection mode |
| `multiSelectPlaceholderCount` | `boolean` | `false` | Show count in placeholder when multi-selecting |
| `template` | `TemplateRef<any>` | — | Custom template for options |
| `hasEmptyOption` | `boolean` | `false` | Add empty option (single-select only) |
| `emptyOptionText` | `string` | `''` | Text for empty option |
| `nomargin` | `boolean` | `false` | Remove host margin |
| `tooltipText` | `string` | `''` | Hover tooltip |
| `tabIndex` | `number` | — | Tab index |
| `disabled` | `boolean` | `false` | Disabled state |

When using object options, provide a `template` to render the display text. The component **cannot be self-closed** when it has an `<ng-template>` child.

---

## Checkbox — `al-ds-checkbox`

**Import:** `AlSelectorModule` · Implements `ControlValueAccessor` directly. **Value type:** `boolean`

⚠️ Does **not** extend `AlInputComponent`. **These inputs do NOT exist:** `placeholder`, `isRequired`, `isReadonly`, `showErrors`, `name`, `value`.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Label text (or use `<ng-content>`) |
| `disabled` | `boolean` | `false` | Disabled state |
| `multiple` | `'none' \| 'set' \| 'full'` | — | `'none'` = standalone, `'set'` = group member, `'full'` = "select all" |

Group checkboxes with a `FormArray`, setting `[formControlName]` to each control's index (`0`, `1`, `2`, …). Use a separate `FormControl` for the "select all" checkbox.

### `[lock]` directive

**Selector:** `al-ds-checkbox[lock]` · **Import:** `AlSelectorModule`

Adds `[locked]="true"` to show a visual locked state.

---

## Radio Button — `al-ds-radio`

**Import:** `AlSelectorModule` · Implements `ControlValueAccessor` via `NgControl`.

⚠️ Does **not** extend `AlInputComponent`. **These inputs do NOT exist:** `placeholder`, `isReadonly`, `showErrors`.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Label (or `<ng-content>`). Appends `*` when `isRequired` is `true`. |
| `value` | `any` | — | Value this radio represents |
| `name` | `string` | — | Native name (auto-set by `formControlName`) |
| `isRequired` | `boolean` | `false` | Required `*` indicator |
| `disabled` | `boolean` | `false` | Disabled state |

Group by giving all radios the same `formControlName`.

---

## Switch — `al-ds-switch`

**Import:** `AlSwitchesModule` · Implements `ControlValueAccessor` directly. **Value type:** `boolean`

⚠️ Does **not** extend `AlInputComponent`. **These inputs do NOT exist:** `placeholder`, `isRequired`, `isReadonly`, `name`, `showErrors`.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Label text |
| `showLabelAbove` | `boolean` | `false` | Position label above the switch |
| `singleLine` | `boolean` | `false` | Adds `single-line` CSS class |

Disable via `formControl.disable()` or `setDisabledState`.

⚠️ **`labelPosition` does NOT exist.** Always use `showLabelAbove`.

---

## Input Autocomplete — `al-ds-input[al-ds-autocomplete]`

**Import:** `AlInputAutocompleteModule` (also requires `AlInputModule`) · Directive applied to `al-ds-input` that adds a dropdown with autocomplete suggestions.

⚠️ This is a **directive** on `al-ds-input`, not a standalone component. The dropdown (`al-input-autocomplete-dropdown`) is created dynamically.

| Input | Type | Default | Description |
|---|---|---|---|
| `options` | `any[]` | — | Autocomplete suggestion items |
| `debounceTime` | `number` | `500` | Debounce delay (ms) before emitting search |
| `template` | `TemplateRef<any>` | — | Custom template for rendering options |
| `autocompleteOff` | `boolean` | `true` | Disables native browser autocomplete |
| `enableFocus` | `boolean` | `false` | Opens dropdown on focus |

| Output | Type | Description |
|---|---|---|
| `search` | `string` | Emitted with search text (debounced) |
| `select-option` | `any` | Emitted when an option is selected |

Supports keyboard navigation: Arrow Up/Down to navigate, Enter/Tab to select.

---

## Submit Button — `al-ds-button`

**See also:** `ace-angular-core-components` skill for full `al-ds-button` documentation.

Use `al-ds-button` instead of a native `<button>` for form submission. **Import:** `AlButtonModule` from `@alphabet/core-components`.

| Input | Type | Default | Description |
|---|---|---|---|
| `label` | `string` | — | Button label text |
| `type` | `AlButtonComponentType` | `'outlined'` | `'outlined'` \| `'primary'` \| `'ghost'` \| `'danger'` |
| `disabled` | `boolean` | `false` | Disabled state |
| `loading` | `boolean` | `false` | Shows loading spinner |

| Output | Type | Description |
|---|---|---|
| `clickEvent` | `Event` | Click event (use instead of native `(click)`) |

⚠️ **Choose one submit mechanism:** either `(ngSubmit)` on the `<form>` **or** `(clickEvent)` on the button — never both, or the handler fires twice.

---

## Directives

### `[eager]` — Eager Input

**Selector:** `al-ds-input[eager]`, `al-ds-input-number[eager]` · **Import:** `AlInputModule`

Triggers change detection on every keypress instead of blur. Optional debounce value.

### `[al-ds-no-decimal]` — No Decimal

**Selector:** `al-ds-input-number[al-ds-no-decimal]` · **Import:** `AlInputModule`

Prevents decimal input in number fields.

### `[uppercase]` — Uppercase

**Selector:** `[uppercase]` · **Import:** `AlUppercaseDirective` (standalone)

Transforms input to uppercase on keypress.
