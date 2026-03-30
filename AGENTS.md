# Agent Guidelines

## Response Language

Respond to the user in **Japanese**. Code comments (doc / impl) in Japanese. Identifiers and port names in English.

## Core Principles

- **Do NOT maintain backward compatibility** unless explicitly requested. Break things boldly.
- **Keep this file under 30-40 lines of instructions.** Every line competes for the agent's limited context budget (~150-200 total).

## CONVENTIONS

- Delete dead code immediately
- **Port naming**: Use `clk` for clock and `rst` for reset ports.
- For other ports, prefer semantic names without `i_`/`o_` when direction is obvious.
- Use `i_`/`o_` only for short or ambiguous names, or to match external/std interfaces.
- **Reserved words**: If `reset` or `clock` names are necessary, escape as `r#reset` or `r#clock`.

## ANTI-PATTERNS (THIS PROJECT)

- Do not edit generated outputs under `target/` or `doc/` by hand.
- Do not edit vendored stdlib under `dependencies/` directly; regenerate upstream.
- Do not re-implement basic functions (Synchronizer, EdgeDetector, FIFO, etc.) that are available in [Veryl std](https://github.com/veryl-lang/veryl/tree/master/crates/std/veryl/src).

## COMMANDS

```bash
veryl fmt # format code
veryl check
veryl build
veryl test # simulation and tests
```
