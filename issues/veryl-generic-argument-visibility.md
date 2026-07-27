# Veryl issue draft

## Title

Can a module parameter be used as a generic argument across packages?

## Body

With Veryl `0.20.2-nightly` (`306c891`, 2026-07-26), the minimal project in
[`veryl-generic-cross-package-repro`](./veryl-generic-cross-package-repro) fails on `veryl check`.

The callee defines:

```veryl
pub package Generic {
    function identity::<WIDTH: u32> (
        value: input logic<WIDTH>,
    ) -> logic<WIDTH> {
        return value;
    }
}
```

The caller uses its module parameter as the generic argument:

```veryl
pub module Caller #(param WIDTH: u32 = 8) (
    value: input logic<WIDTH>,
    result: output logic<WIDTH>,
) {
    always_comb {
        result = callee::Generic::identity::<WIDTH>(value);
    }
}
```

The error is:

```text
unresolvable_generic_expression
"WIDTH" can't be resolved from the definition of generics

referring_before_definition
"WIDTH" is referred before it is defined
```

Changing `::<WIDTH>` to `::<8>` passes, and the callee passes when checked by itself.

The [generics documentation](https://doc.veryl-lang.org/book/05_language_reference/14_generics.html)
says that local parameters cannot be used as generic arguments in some cases. Is this case
intentionally unsupported? If so, what is the recommended pattern for a package function whose
width depends on a caller module parameter?

I found this while `interpolation` was calling `fixedpoint::SignedFixedPointRaw::resize` with
module-dependent widths. For now, each interpolator has a private helper with the same resize
logic. I would like to remove those helpers if this use case becomes supported.
