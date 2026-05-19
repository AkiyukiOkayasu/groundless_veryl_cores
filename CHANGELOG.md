# Changelog

## [Unreleased]

### Added

- `Phasor`に`eoc_out`（End Of Cycle）パルス出力を追加
  - 位相ラップアラウンド検出による1サイクルパルス
  - オシレーターシンク用途での使用を想定
- `Phasor`に位相ゼロリセット（`phase_rst`）を追加（同期ロジック）
- `PinkNoise`モジュールを追加（Voss-McCartney + Xorshift32）
  - 24段構成、単一Xorshift32フリーラン
  - サンプルカウンタの各ビット立ち上がりで該当行をラッチ
  - 出力: 24行加算 → ÷8 → Q8.24 (RMS ≈ 0.35, WhiteNoise比-4.2dB)

### Changed

- `tools/release.sh`を削除し`.githooks/pre-push`に移行
  - バージョンタグpush時にCHANGELOG更新漏れを検知して中断
- `Phasor`の位相リセットを`reset`型から`logic`型に変更
  - システムリセットと位相リセットを分離
  - 同期リセットによりタイミングを明確化
- 全オシレーターモジュールの位相リセットポートを`phase_rst: input logic`に変更
  - `SineOscillator` / `SineOscillatorLerp`
  - `SawOscillator`
  - `TriangleOscillator`
  - `PwmSquareOscillator`
  - `MultiWaveOscillator`
