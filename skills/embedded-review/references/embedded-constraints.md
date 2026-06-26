# Embedded Systems Constraints

Common constraints for code running on embedded systems (microcontrollers,
ECUs, real-time platforms). Apply these as baseline rules during review.
Callers may add or relax constraints for their specific domain.

## Memory Constraints

### No Dynamic Memory Allocation (Production Code)

- **Rule**: No `new`, `delete`, `malloc`, `free`, `calloc`, `realloc` in
  production code.
- **Includes**: No STL containers that allocate (`std::vector`, `std::string`,
  `std::map`, `std::unordered_map`, `std::list`, etc.) unless they use a
  static/pool allocator.
- **Allowed alternatives**: `std::array`, `std::string_view`, fixed-size
  buffers, placement new with pre-allocated memory.
- **Tests are typically exempt** from this rule (check with domain owner).
- **Rationale**: Embedded systems have limited RAM, no virtual memory, and
  heap fragmentation can cause unpredictable failures.

### Stack Usage

- Stack size is fixed and limited (often 1–8 KB per task/thread).
- Avoid large local variables (arrays, structs) — prefer static allocation
  or pass by reference.
- No variable-length arrays (VLAs).
- No deep or unbounded recursion.
- Recursive algorithms must have a proven bounded depth.

### Static Allocation

- Prefer `static` or file-scope variables for long-lived data.
- Use `constexpr` for compile-time constants.
- Buffer sizes should be defined as named constants with `static_assert`
  validation where possible.

## Real-Time Constraints

### Interrupt Service Routines (ISRs)

- ISRs must be short — set flags, copy data, return.
- No blocking calls in ISRs (no mutexes, no I/O, no logging).
- No dynamic allocation in ISRs.
- Data shared between ISR and main context must use `volatile` or atomics
  with appropriate memory barriers.

### Timing

- Time-critical paths must have bounded worst-case execution time (WCET).
- No unbounded loops or waits in real-time tasks.
- Prefer deterministic algorithms over average-case-fast ones.
- Consider jitter and scheduling latency for periodic tasks.

### Blocking & Synchronization

- Minimize critical section duration.
- Prefer lock-free data structures where possible.
- Document lock ordering to prevent deadlocks.
- Watchdog timers should not be starved by long computations.

## Hardware Interaction

### Register Access

- Use `volatile` for memory-mapped I/O registers.
- Access registers through a hardware abstraction layer (HAL) where possible.
- Read-modify-write sequences on registers must be atomic or interrupt-safe.

### Peripheral Configuration

- Peripheral initialization must be complete before use.
- DMA transfers must have proper buffer alignment and cache management.
- Pin configurations must match hardware design (pull-ups, drive strength).

### Endianness & Alignment

- Be explicit about byte order when serializing/deserializing bus data.
- Ensure struct packing/alignment matches hardware expectations.
- Use `static_assert(sizeof(...))` to verify struct sizes at compile time.

## Compiler & Toolchain

### Warnings

- Code should compile without warnings at the project's configured warning level.
- Assume `#pragma warning disable` suppressions are acceptable (don't flag them).

### Undefined Behavior

- No reliance on undefined behavior (strict aliasing, signed overflow, etc.).
- No uninitialized reads.
- Use compiler sanitizers in test builds where available.

### Portability

- Avoid compiler-specific extensions unless documented and justified.
- Use `<cstdint>` fixed-width types (`uint8_t`, `int32_t`, etc.) for
  hardware-interfacing code.
- Be aware of `sizeof(int)` and pointer size differences across targets.
