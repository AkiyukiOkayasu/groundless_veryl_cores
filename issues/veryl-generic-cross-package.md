# Veryl issue draft: cross-package generic function and module parameter

## Title

Cross-package generic function call rejects a caller module parameter

## Environment

- Veryl: `0.20.2-nightly` (`306c891`, 2026-07-26)
- macOS

## Reproduction

The complete minimal reproduction is in
[`issues/veryl-generic-cross-package-repro`](./veryl-generic-cross-package-repro).
It consists of one callee package, one caller package, and no standard-library dependency.

### `callee/Veryl.toml`

```toml
[project]
name = "gndless_generic_callee"
version = "0.1.0"

[build]
sources = ["src"]
target = { type = "directory", path = "target" }

[test]
```

### `callee/src/generic.veryl`

```veryl
pub package Generic {
    function identity::<WIDTH: u32> (
        value: input logic<WIDTH>,
    ) -> logic<WIDTH> {
        return value;
    }
}
```

### `caller/Veryl.toml`

```toml
[project]
name = "gndless_generic_caller"
version = "0.1.0"

[build]
sources = ["src"]
target = { type = "directory", path = "target" }

[test]

[dependencies]
callee = { path = "../callee" }
```

### `caller/src/caller.veryl`

```veryl
pub module Caller #(
    param WIDTH: u32 = 8,
) (
    value: input  logic<WIDTH>,
    result: output logic<WIDTH>,
) {
    always_comb {
        result = callee::Generic::identity::<WIDTH>(value);
    }
}
```

Run:

```text
cd caller
veryl check
```

## Actual result

`veryl check` fails with:

```text
unresolvable_generic_expression
"WIDTH" can't be resolved from the definition of generics

referring_before_definition
"WIDTH" is referred before it is defined
```

The first diagnostic points to `Caller::WIDTH` at the generic call site. The second points to
the return type of `Generic::identity` in the callee package. The callee package itself passes
`veryl check`.

Replacing `::<WIDTH>` with the literal `::<8>` makes this minimal example pass. A generic module
instantiation using a module parameter is not part of this reproduction.

## Expected result

Please either:

1. support a caller module parameter as a generic function argument across a package boundary; or
2. document this as an intentional limitation and provide a precise diagnostic and supported
   workaround.

The current generics documentation already notes that local parameters cannot be used as generic
arguments in many cases. This report narrows that limitation to a two-package generic function
call and asks whether this case is expected. See:
<https://doc.veryl-lang.org/book/05_language_reference/14_generics.html>

## Related reports checked

The following reports are related but describe different failures:

- [#3104](https://github.com/veryl-lang/veryl/issues/3104): an item imported from a generic
  package defined in another project is reported as an unknown member.
- [#2683](https://github.com/veryl-lang/veryl/issues/2683): resolving a path containing a package
  alias and a package-defined `gen` constant fails.
- [#2412](https://github.com/veryl-lang/veryl/pull/2412): introduces `gen` declarations; it is not
  a report about this generic function call.

I did not find an existing Issue or PR for this exact two-package reproduction.

## Workaround in the consuming project

The consuming project temporarily duplicates `fixedpoint::SignedFixedPointRaw::resize` inside
the interpolation package. The duplicate functions are marked with
`TODO(veryl-generic-cross-package)` so they can be removed if this case becomes supported.
