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
呼び出しは現行toolchainで解決できません。そのため、module内にあった2つの重複helperを
削除し、`linear_interpolator.veryl`のproject-scopeに`resize_interpolation_global`を
1つだけ置いて、linearとcubicの両方から使っています。この関数は利用者向けの数値API
ではなく、cross-package呼び出しが可能になるまでのworkaroundです。丸めとoverflowの
意味論は`SignedFixedPointRaw::resize`と一致させています。linearの`NUM_WIDTH`とcubicの
`NUM_WIDTH`／`OUTPUT_SHIFT`は、この呼び出しに必要な導出constであり、moduleの設定値では
ありません。

Veryl側でcross-packageのgeneric呼び出しがサポートされたら、次の順でこのworkaroundを
削除します。

1. `resize_interpolation_global`を削除する。
2. linear／cubicの呼び出しを`fixedpoint::SignedFixedPointRaw::resize::<...>`へ置き換える。
3. 全rounding mode、cubicのsaturation／wrap、小幅全探索、benchmarkの結果を比較する。
4. interpolation packageとroot integrationの`veryl fmt`／`check`／`test`／`build`／
   `doc`を実行する。

```veryl
inst interp: interpolation::CubicLagrangeInterpolator (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。benchmarkは固定vectorのみを使い、oscillatorへ依存しません。
