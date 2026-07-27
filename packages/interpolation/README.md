# gndless_interpolation

sample windowを受け取るcombinational補間kernelです。ASRCのFIFO、phase accumulator、filterは所有しません。

公開APIは`ZeroOrderHold`、`LinearInterpolator`、`CubicLagrangeInterpolator`です。`fixedpoint`に依存しますが、現行の補間portはsigned sampleとunsigned Q0.`PHASE_WIDTH` phaseを直接扱います。全方式のlatencyは0です。

linearはphase 0〜最大をsample0からsample1へ線形移動し、default roundingはnearest ties to evenです。cubicは`sample_m1`、`sample0`、`sample1`、`sample2`の4点3次LagrangeをHorner形式で評価し、全幅演算後に一度だけ丸め、default overflowはsaturationです。係数はQ2.16量子化です。

## Veryl generic制約への一時対応

`LinearInterpolator`と`CubicLagrangeInterpolator`には、fixedpoint packageの
`SignedFixedPointRaw::resize`を直接呼ばず、同じ処理をpackage内で行う
`resize_interpolation` adapterがあります。これは仕様上の別実装ではなく、Veryl
0.20.2-nightlyでmodule parameter／constをcross-package generic引数へ渡した際に
発生する`unresolvable_generic_expression`と`referring_before_definition`を回避する
ための一時措置です。

根本修正が入ったら、ソース中の
`TODO(veryl-generic-cross-package)`を検索し、adapterを削除して
`fixedpoint::SignedFixedPointRaw::resize::<...>`へ戻してください。削除前に、
全rounding mode、cubicのsaturation／wrap、小幅全探索、benchmarkの結果が一致する
ことを確認し、interpolation packageとroot integrationの`veryl check`／`test`／
`build`／`doc`を再実行します。再現条件と期待する修正は
[`issues/veryl-generic-cross-package.md`](../../issues/veryl-generic-cross-package.md)
にまとめています。

```veryl
inst interp: interpolation::CubicLagrangeInterpolator (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。benchmarkは固定vectorのみを使い、oscillatorへ依存しません。
