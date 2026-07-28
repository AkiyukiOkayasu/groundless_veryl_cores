# gndless_interpolation

sample windowを受け取るcombinational補間kernelです。ASRCのFIFO、phase accumulator、filterは所有しません。

公開APIは`LinearInterpolator`と`CubicLagrangeInterpolator`です。`fixedpoint`に依存しますが、現行の補間portはsigned sampleとunsigned Q0.`PHASE_WIDTH` phaseを直接扱います。全方式のlatencyは0です。0次ホールドは公開kernelにせず、比較ベンチマーク内の`BenchmarkZeroOrderHold`としてのみ保持します。

linearはphase 0〜最大をsample0からsample1へ線形移動し、default roundingはnearest ties to evenです。cubicは`sample_m1`、`sample0`、`sample1`、`sample2`の4点3次LagrangeをHorner形式で評価し、全幅演算後に一度だけ丸め、default overflowはsaturationです。係数はQ2.16量子化です。

linearとcubicの最終的な幅変換には、module parameterを直接受け取れる
`fixedpoint::resize::<...>`を使用します。

```veryl
inst interp: interpolation::CubicLagrangeInterpolator (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。benchmarkは固定vectorのみを使い、oscillatorへ依存しません。
