# RxJS Subscription Cleanup

Angular provides built-in utilities for managing RxJS subscription lifecycles. Always use these to prevent memory leaks.

## `takeUntilDestroyed` (Preferred)

Use `takeUntilDestroyed` from `@angular/core/rxjs-interop` to automatically complete observables when a component, directive, or service is destroyed.

### In injection context (field initializer)

When called during construction (field initializer or `inject()` context), no argument is needed:

```ts
import { Component, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormBuilder } from '@angular/forms';
import { debounceTime } from 'rxjs';

@Component({ ... })
export class SettingsComponent {
  readonly #settingsService = inject(SettingsService);
  readonly form = inject(FormBuilder).group({ /* ... */ });

  readonly #autoSave = this.form.valueChanges.pipe(
    debounceTime(500),
    switchMap(value => this.#settingsService.saveDraft(value)),
    takeUntilDestroyed() // No argument needed in injection context
  ).subscribe();
}
```

### Outside injection context (e.g., method calls)

When subscribing outside the constructor/field initializer, inject `DestroyRef` and pass it explicitly:

```ts
import { Component, DestroyRef, inject } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { OrderService } from './order.service';

@Component({ ... })
export class OrderComponent {
  readonly #destroyRef = inject(DestroyRef);
  readonly #orderService = inject(OrderService);

  submitOrder(order: Order): void {
    this.#orderService
      .create(order)
      .pipe(takeUntilDestroyed(this.#destroyRef))
      .subscribe(response => { /* handle success */ });
  }
}
```

## Deprecated: `componentDestroyed()`

The `componentDestroyed()` helper from `@alphabet/core-components` is **deprecated**. Replace it with `takeUntilDestroyed`:

```ts
// ❌ DEPRECATED
import { componentDestroyed } from '@alphabet/core-components';
// ...
.pipe(takeUntil(componentDestroyed(this.#destroyRef)))

// ✅ MODERN
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
// ...
.pipe(takeUntilDestroyed(this.#destroyRef))
```

## `DestroyRef` directly

For advanced use cases (e.g., custom cleanup logic beyond RxJS), use `DestroyRef.onDestroy()`:

```ts
import { Component, DestroyRef, inject } from '@angular/core';

@Component({ ... })
export class MyComponent {
  readonly #destroyRef = inject(DestroyRef);

  constructor() {
    const interval = setInterval(() => { /* ... */ }, 1000);
    this.#destroyRef.onDestroy(() => clearInterval(interval));
  }
}
```

## When to use which

| Scenario | Approach |
|----------|----------|
| Observable in field initializer | `takeUntilDestroyed()` (no arg) |
| Observable in methods (e.g., POST calls) | `takeUntilDestroyed(this.#destroyRef)` |
| Non-RxJS cleanup (timers, DOM listeners) | `DestroyRef.onDestroy(() => ...)` |
| Signals with async data | Prefer `toSignal()` by default; use `resource()` when appropriate (currently experimental) — no manual cleanup needed |

## Key rules

1. **`takeUntilDestroyed` is only needed when you explicitly `.subscribe()`** — if the observable is consumed via `toSignal()`, `async` pipe, or `resource()`, unsubscription is handled automatically
2. **Prefer signals over manual subscriptions** — `toSignal()`, `resource()`, and `computed()` handle Observable subscription cleanup automatically
3. **Never use `takeUntil(componentDestroyed(...))` in new code** — use `takeUntilDestroyed` instead
4. **Always inject DestroyRef with `#` prefix**: `readonly #destroyRef = inject(DestroyRef);`
