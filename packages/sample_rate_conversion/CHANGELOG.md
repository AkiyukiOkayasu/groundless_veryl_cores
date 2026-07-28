# Changelog

## [Unreleased]

- 公開moduleのparam/port doc commentを追加し、説明文の途中改行を整理
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary表記を統一
- 各testのdoc commentを検証目的が分かる表現へ統一
### Changed

- 固定レートASRC benchmarkの入力を48点の固定正弦波vectorへ変更し、`oscillator`依存を削除
- 固定レートASRC benchmarkと解析スクリプトをpackageへ移動
- package名を`asrc`から`sample_rate_conversion`へ変更し、同期型sample-rate converterも収容できる構成へ整理
- ASRC本体を独立packageへ移動
- `FarrowAsrc`を`CubicLagrangeAsrc`へ改名
- 補間、phase accumulator、halfbandを依存packageへ分離
- 補間kernelのdefault nearest ties to even変更に合わせ、cubic統合goldenを更新
- Linear ASRCの起動・窓補充・underflowと4倍HBF経路のburstを示すWavedromを追加
- `SampleRateTracker`の測定開始、`period_valid`、lock獲得を示すWavedromを追加
