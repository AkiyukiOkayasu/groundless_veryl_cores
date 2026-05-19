# Agent Guidelines

## Response Language

Respond to the user in **Japanese**. Code comments (doc / impl) in Japanese. Identifiers and port names in English.

## Core Principles

- **Do NOT maintain backward compatibility** unless explicitly requested. Break things boldly.
- **Keep this file under 30-40 lines of instructions.** Every line competes for the agent's limited context budget (~150-200 total).

## CONVENTIONS

- Delete dead code immediately
- **Port naming**: Use bare semantic names only (e.g. `clk`, `rst`, `phase`, `data`, `valid`, `audio`). Do NOT use `i_`/`o_` prefixes or `_in`/`_out` suffixes — the `input`/`output` type already conveys direction.
- System reset uses `rst` (Veryl `reset` type). Functional resets (phase reset, etc.) use `logic` type with semantic names like `phase_rst`.
- Exception: std interface ports (e.g. `$std::synchronizer_basic`'s `i_clk`, `i_d`, `o_d`) use their library-defined names.
- **Naming style**: File names are `snake_case`; public modules are `UpperCamelCase`; functions, locals, instances, and ports are `snake_case`; params and constants are `UPPER_SNAKE_CASE`; package names may use `PascalCase`.
- **Reserved words**: If `reset` or `clock` names are necessary, escape as `r#reset` or `r#clock`.

## ANTI-PATTERNS (THIS PROJECT)

- Do not edit generated outputs under `target/` or `doc/` by hand.
- Do not edit vendored stdlib under `dependencies/` directly; regenerate upstream.
- Do not re-implement basic functions (Synchronizer, EdgeDetector, FIFO, etc.) that are available in [Veryl std](https://github.com/veryl-lang/veryl/tree/master/crates/std/veryl/src).

## MANDATORY: RTL編集後の検証パイプライン

`.veryl`ファイルを編集した後は、**必ず**以下を順番に実行すること:
1. `veryl fmt` → 2. `veryl check` → 3. `veryl test` → 4. CHANGELOG.mdの`[Unreleased]`に追記
- 失敗したら修正して再実行
- 複数ファイル編集時は全編集完了後に1回だけ実行
- RTL以外のみの編集はパイプライン不要

## OTHER COMMANDS

- When tagging a release, update `version` in Veryl.toml and move `[Unreleased]` entries into new version section matching the tag
- `veryl build` / `veryl publish`
- Run `git config core.hooksPath .githooks` after clone to enable pre-push CHANGELOG enforcement
