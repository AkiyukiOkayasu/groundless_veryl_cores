# gndless_delta_sigma

Q1.31 PCMを1bit PDMへ変換する1次・2次delta-sigma modulatorです。公開APIは`DeltaSigma1st`と`DeltaSigma2nd`、依存は`fixedpoint`です。

入力は`fixedpoint::Q1_31::Raw`（-1.0以上、+1.0未満）、出力は常に1bitです。stateは同期resetで初期化し、`enable`停止中は保持します。内部gain、overflow、長時間densityの契約はmodule doc commentとNative testで固定しています。

```veryl
inst modulator: delta_sigma::DeltaSigma2nd (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
