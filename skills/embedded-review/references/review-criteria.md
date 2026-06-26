# Embedded C/C++ Review Criteria

Structured checklist for reviewing embedded C/C++ code. Apply all categories
to every review. Mark items as compliant, non-compliant, or not applicable.

## Critical Issues

These must be addressed before merge.

### Security & Safety

- [ ] No buffer overflows or out-of-bounds access
- [ ] No use-after-free or dangling pointer dereference
- [ ] No uninitialized variable reads
- [ ] No integer overflow/underflow in safety-critical paths
- [ ] Input validation on all external data (bus messages, sensor readings, calibration values)
- [ ] No unchecked casts that could truncate or reinterpret data unsafely

### Runtime Correctness

- [ ] No undefined behavior (strict aliasing, signed overflow, null dereference)
- [ ] Logic correctness — does the code do what the requirements specify?
- [ ] Edge cases handled (boundary values, empty inputs, error returns)
- [ ] Error codes and return values checked consistently
- [ ] Assertions or static_asserts used for invariants where appropriate

### Memory Management

- [ ] No dynamic memory allocation in production code (no `new`, `malloc`, `std::vector` resize, etc.) — tests may be exempt
- [ ] Stack usage is bounded and predictable (no VLAs, no deep/unbounded recursion)
- [ ] Static buffers are sized correctly with compile-time checks where possible
- [ ] No memory leaks in test code (even if dynamic allocation is allowed there)
- [ ] Placement new used correctly if applicable

### Concurrency & Interrupt Safety

- [ ] Shared data protected by appropriate synchronization (mutexes, atomics, disable-interrupt guards)
- [ ] No data races between ISR and main context
- [ ] `volatile` used correctly for hardware registers and ISR-shared variables
- [ ] No blocking calls inside interrupt service routines
- [ ] Critical sections are minimal in duration
- [ ] Lock ordering is consistent (no deadlock risk)

### Performance

- [ ] No unnecessary copies of large objects — use references or move semantics
- [ ] Hot paths are efficient (no unnecessary allocations, syscalls, or I/O)
- [ ] Algorithmic complexity is appropriate for the data size
- [ ] No busy-waiting where event-driven or interrupt-driven approaches are available
- [ ] Timing constraints met (if applicable)

## Code Quality

### Language Conventions

- [ ] Follows the project's C++ standard (specified by caller)
- [ ] Modern C++ idioms used where appropriate (RAII, `auto`, range-based for, `constexpr`)
- [ ] `const` correctness — parameters, member functions, and variables marked `const` where possible
- [ ] `enum class` preferred over plain `enum`
- [ ] No C-style casts — use `static_cast`, `reinterpret_cast` (with justification), `const_cast` (rare)
- [ ] Headers include only what they need (no transitive dependency reliance)
- [ ] Include guards or `#pragma once` present

### Design & Architecture

- [ ] Single responsibility — each class/function does one thing
- [ ] Appropriate abstraction level (not too granular, not god-objects)
- [ ] Dependencies are explicit and direction is clear (no circular dependencies)
- [ ] Hardware abstraction layer (HAL) separates hardware access from business logic
- [ ] Design patterns used appropriately (not over-engineered)

### Naming & Readability

- [ ] Names are descriptive and consistent with project conventions
- [ ] Functions are short enough to understand at a glance
- [ ] Complex logic is commented or decomposed into well-named helpers
- [ ] No magic numbers — use named constants or `constexpr`
- [ ] File organization follows project structure conventions

### Documentation

- [ ] Public API has doc comments (Doxygen or equivalent)
- [ ] Non-obvious algorithms or workarounds are explained
- [ ] TODO comments reference a ticket or have clear context
- [ ] Copyright/license headers present if required by the project

### Testing

- [ ] New functionality has corresponding unit tests
- [ ] Edge cases and error paths are tested
- [ ] Tests are deterministic (no timing-dependent assertions without tolerance)
- [ ] Test names describe the scenario and expected outcome
- [ ] Mock/stub boundaries are appropriate (not mocking implementation details)

## Maintainability

- [ ] No code duplication — shared logic extracted into reusable functions
- [ ] Cyclomatic complexity is reasonable (consider splitting complex functions)
- [ ] Dependencies are minimal and well-justified
- [ ] Code is extensible without requiring modification of existing code (open-closed)
- [ ] No unnecessary coupling between modules
- [ ] Technical debt is not increased without justification
- [ ] Backward compatibility considered (if applicable)
