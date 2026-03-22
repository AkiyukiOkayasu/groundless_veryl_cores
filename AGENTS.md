# Agent Guidelines

## Core Principles

- **Do NOT maintain backward compatibility** unless explicitly requested. Break things boldly.
- **Keep this file under 20-30 lines of instructions.** Every line competes for the agent's limited context budget (~150-200 total).

## CONVENTIONS

- Doc comments and implementation comments are Japanese; identifiers/ports are English.
- Delete dead code immediately
- **Port naming**: Use `clk` for clock and `rst` for reset ports.
- **Reserved words**: If `reset` or `clock` names are necessary, escape as `r#reset` or `r#clock`.

## ANTI-PATTERNS (THIS PROJECT)

- Do not edit generated outputs under `target/` or `doc/` by hand.
- Do not edit vendored stdlib under `dependencies/std/` directly; regenerate upstream.

## COMMANDS

```bash
# Format/build
veryl fmt
veryl check
veryl build
veryl clean

# Simulation + tests
veryl test
```
