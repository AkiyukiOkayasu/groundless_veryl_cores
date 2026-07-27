# Veryl cross-package generic minimal reproduction

`callee` exposes one generic function. `caller` passes its module parameter to that function
through a local path dependency.

```text
cd caller
veryl check
```

With Veryl `0.20.2-nightly (306c891 2026-07-26)`, the command fails with
`unresolvable_generic_expression` and a secondary `referring_before_definition` diagnostic.
