# Veryl issue draft

## Title

Can a module parameter be used as a generic argument across packages?

## Body

With Veryl `0.20.2-nightly` (`306c891`, 2026-07-26), running `veryl check` on the two-package
example below fails.

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
intentionally unsupported? Could this restriction change in a future version? If it is expected to
remain, what is the recommended pattern for a package function whose width depends on a caller
module parameter?
