# Changelog

## [Unreleased]

### Added

- 固定小数点共通演算を追加
  - 丸め付き右シフト（truncation / round half up / round half away from zero）
  - signed/unsigned saturation
  - signed/unsigned clamp
  - signed固定小数点resize（小数位置調整 → 丸め → 飽和）
  - signed multiply helper
- 固定小数点Native testを追加
- ADAT RX/TXコアを`src/adat/`へ移行し、groundlessの命名規則に統一
- ADAT内部テストをVeryl Native testへ移行
- ADATの利用例とNRZI説明を現行API名に更新
- `AdatTx`にフレーム送信完了パルスを追加し、TX→RXイベント駆動ループバックテストを追加
- S/MUX2用の`Smux2Packer`/`Smux2Unpacker`とNative往復テストを追加
- `DeltaSigma1st`/`DeltaSigma2nd`を追加し、Q1.31入力に対するPDM密度をNative testで検証
- IEC 60958共通型、S/PDIF型、AES3型とchannel status生成関数を追加
- Smux2とデルタシグマのNative testを各実装ファイルへ統合
- IEC 60958共通BMC送受信器とNativeループバックテストを追加

### Changed

- Veryl Native testを現行APIに更新し、`rst.assert()`とenum member importを採用
- フィルタテストの収束条件を`$assert`で検証し、矩形波・三角波・ノコギリ波コアのNative testを追加
- CIに生成チェックとNative backend間の整合性検証を追加

## [0.5.1] - 2026-05-20

### Added

- HPF（ハイパスフィルタ）モジュール群を追加 (`src/filter/hpf_shift.veryl`)
  - `HpfShiftSigned`: 固定シフト量・符号付き
  - `HpfShiftVariableSigned`: 可変シフト量・符号付き
  - `HpfShiftUnsigned`: 固定シフト量・符号なし
  - `HpfShiftVariableUnsigned`: 可変シフト量・符号なし
  - LPF出力を入力から減算する構成: `y = x - lpf(x)`

## [0.5.0] - 2026-05-19

### Added

- `.githooks/pre-commit`を追加 — .veryl ファイルの staged 変更時に `veryl fmt` → `veryl check` → `veryl test` を自動実行

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
