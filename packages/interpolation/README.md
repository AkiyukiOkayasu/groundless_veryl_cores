# gndless_interpolation

sample windowを受け取るcombinational補間kernelです。ASRCのFIFO、phase accumulator、filterは所有しません。

公開APIは`ZeroOrderHold`、`LinearInterpolator`、`CubicLagrangeInterpolator`です。`fixedpoint`に依存しますが、現行の補間portはsigned sampleとunsigned Q0.`PHASE_WIDTH` phaseを直接扱います。全方式のlatencyは0です。

linearはphase 0〜最大をsample0からsample1へ線形移動し、default roundingはnearest ties to evenです。cubicは`sample_m1`、`sample0`、`sample1`、`sample2`の4点3次LagrangeをHorner形式で評価し、全幅演算後に一度だけ丸め、default overflowはsaturationです。係数はQ2.16量子化です。

## Verylのgeneric引数可視性制約

[Veryl #3110](https://github.com/veryl-lang/veryl/issues/3110)の回答では、生成される
SystemVerilogの制約により、module／interface／packageの外で定義した関数のgeneric引数
に限ってmodule parameterを渡せる、と説明されています。これはVerylの仕様上の制約で、
[それ以前の議論](https://github.com/veryl-lang/veryl/issues/2088)と標準ライブラリの
`$std::mux`が同じ設計例です。

このprojectで確認した限り、project-scope関数への変更だけでは、interpolationから
別packageの`fixedpoint::SignedFixedPointRaw::resize`へmodule由来のgeneric引数を渡す
呼び出しは解決できません。そのため`resize`本体を`fixedpoint` project直下の
project-scope functionへ移し、linearとcubicから`fixedpoint::resize::<...>`を直接
呼び出しています。`SignedFixedPointRaw`内にresizeの複製やadapterはありません。

この構成はVeryl #3110の制約に合わせたfixedpointの公開APIです。Veryl側でpackage内の
functionにもmodule parameterを渡せるようになった場合は、APIの整理としてresizeを
`SignedFixedPointRaw`へ戻す選択肢がありますが、現時点でinterpolation側の変更は不要です。

```veryl
inst interp: interpolation::CubicLagrangeInterpolator (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。benchmarkは固定vectorのみを使い、oscillatorへ依存しません。
