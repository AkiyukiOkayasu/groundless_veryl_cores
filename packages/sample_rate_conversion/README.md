# gndless_sample_rate_conversion

同期・非同期のsample-rate converterを所有します。現在の公開APIはFIFOを用いた分数比変換の`LinearAsrc`、`ContinuousLinearAsrc`、`CubicLagrangeAsrc`、`FourXHalfbandAsrc`、`SampleRateTracker`です。今後、同期型のsample-rate converterもこのpackageへ追加します。補間kernelは`interpolation`、phase進行は`nco`、4倍経路は`filter`へ委譲します。

依存は`fixedpoint`、`interpolation`、`nco`、`filter`です。入力の受理は`input_valid && input_ready`、出力はmoduleごとのoutput tickまたは連続clockで進みます。ratioは整数3bitを含むQ形式、FIFO depthとstartup levelはparameter、underflowはstickyです。window初期化、advance 0〜4、refill、stall/再開、latencyは各module doc commentを正とします。固定レートbenchmarkは48点の固定正弦波vectorを使用し、試験専用の外部packageには依存しません。

```veryl
inst asrc: sample_rate_conversion::CubicLagrangeAsrc (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。

固定レートの実レート比比較はignored testでCSVを生成し、標準Pythonの解析スクリプトで直接線形補間と4倍HBF経路の振幅を比較します。

```text
veryl test --ignored -t fixed_rate_asrc_benchmark
python3 tools/analyze_fixed_rate_asrc.py target/fixed_rate_asrc_benchmark.csv
```
