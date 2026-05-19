# Changelog

## [Unreleased]

### Changed

- 全ポート名をbare（方向マーカーなし）に統一
  - オシレータ出力: `pcm_out` → `audio`（全14モジュール）
  - Phasor制御出力: `eoc_out` → `eoc`
  - UartRx/MidiRx: `i_rx`/`o_data`/`o_valid` → `rx`/`data`/`valid`
- `SineWaveCore` / `SineWaveLerpCore`内の内部`let audio`を`audio_q8`にリネーム（ポート名との衝突回避）
- AGENTS.mdのポート命名規則をbare前提に更新

## [0.4.2] - 2026-05-19

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
