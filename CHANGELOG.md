# Changelog

## [Unreleased]

### Added

- 固定小数点共通演算を追加
  - `FixedPoint::RoundingMode` enumによる負方向、零方向、正方向、最近傍各種の丸め
  - `FixedPoint::OverflowMode` enumによるwrap/saturate
  - signed固定小数点の右シフト、飽和、resize、multiply helper
- `SignedFixedPointFormat` protoと`SignedFixedPointFormatOf::<W, F>`によるformat generic APIを追加
- Q1.31/Q2.16/Q3.24/Q8.19/Q8.24を`SignedFixedPointFormat`実装の名前付きpresetへ移行
- project-scopeのgeneric演算を追加し、任意幅とformat-awareの固定小数点処理を提供
- 既存モジュールの固定小数点portと演算をsigned format presetへ移行
- 固定小数点Native testを丸め境界、符号、幅変換、飽和、wrap、format変換、非対称乗算まで拡張
- `NcoTick`/`ClockEnableNco`と分数比clock-enable Native testを追加
- ASRC用`FractionalPhaseAccumulator`と位相wrap／平均進行Native testを追加
- 2倍halfband補間器とQ2.16係数設計スクリプト、burst／ready／DCゲインNative testを追加
- IEC60958のpreamble/payload/stereo sample型とsubframe codecを追加
- IEC60958共通BMC serializer/deserializerとNativeループバックテストを追加
- IEC60958の192-frame block schedulerとpreamble巡回Native testを追加
- S/PDIF/AES3 channel status bit mapperとAES3 professional CRCを追加
- IEC60958共通subframe TX/RX coreを新BMC codecへ接続し、Native loopbackを追加
- AES3 status streamとS/PDIF/AES3のstereo transceiverを追加し、Native loopbackを追加
- S/PDIF/AES3 receiverへblock start pulseを追加し、旧metadata loopbackの回帰assertを追加
- BMC preambleの8cell golden Native testを追加
- `LinearInterpolator`/`CubicLagrangeInterpolator`とFIFO接続型`LinearAsrc`を追加し、Native testを追加
- `ContinuousLinearAsrc`を追加し、STD FIFO／分数位相アキュムレータとの連続出力Native testを追加
- `FourXHalfbandAsrc`を追加し、2段HBF burstから50MHz連続出力までのNative testを追加
- 4サンプル窓の`CubicLagrangeAsrc`を追加し、Linear/Cubic Lagrange ASRCのFIFO補充Native testを追加
- ADAT RX/TXコアを`packages/adat/`へ移行し、groundlessの命名規則に統一
- ADAT内部テストをVeryl Native testへ移行
- ADATの利用例とNRZI説明を現行API名に更新
- `AdatTx`にフレーム送信完了パルスを追加し、TX→RXイベント駆動ループバックテストを追加
- S/MUX2用の`Smux2Packer`/`Smux2Unpacker`とNative往復テストを追加
- `DeltaSigma1st`/`DeltaSigma2nd`を追加し、Q1.31入力に対するPDM密度をNative testで検証
- IEC 60958共通型、S/PDIF型、AES3型とchannel status生成関数を追加
- Smux2とデルタシグマのNative testを各実装ファイルへ統合
- IEC 60958共通BMC送受信器とNativeループバックテストを追加
- IEC 60958共通サブフレーム送受信コアとS/PDIF Nativeループバックテストを追加
- S/PDIF用`SpdifTx`/`SpdifRx`ラッパーとNativeループバックテストを追加
- AES3用`Aes3Tx`/`Aes3Rx`ラッパー、channel status CRC、Nativeループバックテストを追加
- 固定小数点とADATのNative単体テストを各実装ファイルへ統合
- 固定小数点formatのraw表現名を`Value`から`Raw`へ変更し、公開APIへ引数・戻り値・使用例のdocumentation commentを追加
- `ZeroOrderHold`を追加し、Linearとのステップ・ランプ・インパルス比較を行うNativeベンチマークを追加
- `CicDecimator`/`CicInterpolator`と基本動作のNative testを追加
- `SampleRateTracker`を追加し、サンプル到着周期の固定小数点平滑化とロック状態を提供
- 補間ベンチマークCSVを検証・集計する依存パッケージなしの解析スクリプトを追加
- 補間ベンチマークへ0.05／0.15／0.25／0.40 Fsの正弦波ケースを追加
- 補間ベンチマークへCubic Lagrange補間出力と3方式間の誤差・周波数応答解析を追加
- 固定48kHz／50MHz比で直接線形補間と4倍HBF経路を比較するignoredベンチマークを追加
- 固定レートASRCのCSVから正弦波振幅・ゲイン差・残差RMSを求める解析スクリプトを追加

### Changed

- 公開RTLを12個のinner projectへ分割し、ルートをpackage横断integration／benchmark専用projectへ整理
- 全packageをlocal path dependencyで接続し、package単独のfmt/check/test/build/docとbackend validationをCIへ追加
- 補間kernelを`gndless_interpolation`へ移動し、`CubicLagrangeInterpolator`の丸め・overflow policyと小幅全探索testを追加
- `FarrowInterpolator`/`FarrowAsrc`をそれぞれ`CubicLagrangeInterpolator`/`CubicLagrangeAsrc`へ移行し、`spi_pkg`を`Spi`へ改名
- fixedpointのraw generic演算をproject-scopeへ統一し、parameterized moduleから直接利用する構成へ変更
- `SignedFixedPoint` packageを廃止し、`convert`を含む固定小数点演算をflatなproject-scope APIへ統一
- 固定小数点固有でない`clamp`を公開APIから削除し、`round_shift`と`saturate`の実装を`resize`へ統合
- halfband固有の幅変換adapterを削除し、fixedpointのproject-scope `resize`を使用
- 固定小数点実装を`packages/fixedpoint/`の独立Veryl project `gndless_fixedpoint`へ分離し、親projectからlocal path dependencyとして参照
- 固定小数点の丸めモード指定を数値定数から `FixedPoint::RoundingMode` enumへ変更
- 固定小数点formatのassociated typeを`Q1_31::Value`などから`Q1_31::Raw`へ変更
- 固定小数点formatの`WIDTH`/`FRACTION_BITS`/`Raw`および丸め・overflow policyのdocumentation commentを拡充
- ADAT→50MHz差動PDMの高音質化計画を、帯域制限付き4倍オーバーサンプリング、Farrow分数遅延、レート追従、ΔΣ評価の段階構成へ更新
- Cubic Lagrange実装を`packages/interpolation/`と`packages/asrc/`へ、定量ベンチマークを`packages/interpolation/`へ分離
- 公開APIをS/PDIF/AES3のtransceiverと周辺コアに整理し、Sine ROMとIEC60958共通実装moduleをprivate化
- S/PDIFの未実装領域をTODOとして明示し、公開packageとして維持
- 公開moduleとpackageのdocumentation commentを`veryl doc`に関連付け、UART/MIDIレシーバの説明を追加
- 初期のIEC60958 BMC/subframe/S/PDIF/AES3実装を、共通codecとstereo transceiverへ整理
- Veryl Native testを現行APIに更新し、`rst.assert()`とenum member importを採用
- フィルタテストの収束条件を`$assert`で検証し、矩形波・三角波・ノコギリ波コアのNative testを追加
- CIに生成チェックとNative backend間の整合性検証を追加
- `enable`など真偽属性として自然な1bit信号に`bbool`を限定し、ADATの`FrameParser`と`TxFrameBuilder`の重複ロジックを生成ループへ整理
- IEC60958のパリティ・preamble判定とinvalid/lock/error状態を明示的な真偽型へ整理
- NCOの`configured`状態を2値保証された`bbool`へ整理
- ADATのFrameParser/TxFrameBuilder Native testを8チャンネル対象へ拡張し、公開モジュール構成と型方針をREADMEに追記
- 連続ASRCの起動時FIFO蓄積量を設定可能にし、4倍HBFのburstによる起動直後underflowを防止
- ADAT固有のS/MUX2 packer/unpackerを`packages/adat/`へ移動

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
