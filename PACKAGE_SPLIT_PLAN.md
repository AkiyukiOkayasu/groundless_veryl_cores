# Veryl core package分割実装計画

## 1. 目的

`groundless_veryl_cores`に含まれる公開RTLを、責務・依存方向・検証単位が明確な
複数のVeryl inner projectへ分割する。

当面は同一monorepoの`packages/`以下で開発し、APIと数値仕様が安定したpackageから
将来個別のGitHub repositoryへ分離する。今回の実装ではrepository分割および
Veryl package registryへのpublishは行わない。

この計画は別sessionの5.6 Lunaが、追加の設計判断を極力行わずに一括実装できる
ことを目的とする。

## 2. レビュー結論

リポジトリ全体を次の基準でレビューした。

1. 独立した公開契約を一文で説明できる
2. 依存方向を一方向にできる
3. 単独利用者が想定できる
4. 独立した検証方法を持つ
5. 他領域と変更・リリース周期が異なる

結論として、12個の公開packageと1個のルート統合projectへ分割する。
これは現在のディレクトリを機械的にpackage化した結果ではない。

### 2.1 レビューの反復と反対意見の扱い

レビューは次の3観点で行った。

1. 全moduleの責務、再利用先、公開境界
2. Veryl project間の依存DAG、移行順序、生成RTL
3. テスト成熟度、CDC・protocol・DSPリスク、過剰分割への反対レビュー

反対レビューでは、fixedpointとinterpolation以外は公開品質が不足しており、
一括して外部repository化・registry publishすべきではないとの指摘があった。
この指摘を採用し、次を区別する。

- 今回行う: monorepo内のinner project化、依存方向の固定、テスト所有権の分離
- 今回行わない: 外部repository化、registry publish、全packageの大幅なAPI再設計
- 例外: 既に設計レビュー済みのinterpolation数値APIは今回完成させる

inner project化は公開を意味しない。ADAT、IEC60958、filter、oscillatorなどは
境界を物理的に分けるが、独立repositoryへ出す前に本計画の不足テストを満たす。
この二段階化により、ユーザーが求める一括実装と、未成熟APIを早期公開しない
安全性を両立する。

以下は過剰分割になるため行わない。

- CIC、halfband、shift filterを別packageにする
- ADAT Rx、Tx、S/MUXを別packageにする
- IEC 60958、S/PDIF、AES3を別packageにする
- sine、triangle、noiseなど波形ごとに分ける
- NCO tickとphase accumulatorを別packageにする
- 1次と2次delta-sigmaを別packageにする
- linear ASRCとcubic ASRCを別packageにする
- `common`、`audio_types`、`protocol_types`のような型置き場だけのpackageを作る

### 2.2 今回inner projectへ分割するもの

| Directory | Veryl project | Namespace | 将来のrepository |
| --- | --- | --- | --- |
| `packages/fixedpoint` | `gndless_fixedpoint` | `fixedpoint` | `AkiyukiOkayasu/gndless-fixedpoint-veryl` |
| `packages/interpolation` | `gndless_interpolation` | `interpolation` | `AkiyukiOkayasu/gndless-interpolation-veryl` |
| `packages/nco` | `gndless_nco` | `nco` | `AkiyukiOkayasu/gndless-nco-veryl` |
| `packages/filter` | `gndless_filter` | `filter` | `AkiyukiOkayasu/gndless-filter-veryl` |
| `packages/oscillator` | `gndless_oscillator` | `oscillator` | `AkiyukiOkayasu/gndless-oscillator-veryl` |
| `packages/asrc` | `gndless_asrc` | `asrc` | `AkiyukiOkayasu/gndless-asrc-veryl` |
| `packages/delta_sigma` | `gndless_delta_sigma` | `delta_sigma` | `AkiyukiOkayasu/gndless-delta-sigma-veryl` |
| `packages/uart` | `gndless_uart` | `uart` | `AkiyukiOkayasu/gndless-uart-veryl` |
| `packages/midi` | `gndless_midi` | `midi` | `AkiyukiOkayasu/gndless-midi-veryl` |
| `packages/spi` | `gndless_spi` | `spi` | `AkiyukiOkayasu/gndless-spi-veryl` |
| `packages/adat` | `gndless_adat` | `adat` | `AkiyukiOkayasu/gndless-adat-veryl` |
| `packages/iec60958` | `gndless_iec60958` | `iec60958` | `AkiyukiOkayasu/gndless-iec60958-veryl` |

`fixedpoint`は分割済みなので構造を維持し、他packageからの直接参照へ移行する。

`filter`は単数形に統一する。理由は、既存領域名が`filter`であり、
project名、dependency名、将来のrepository名を同じ語幹に保てるためである。

### 2.3 ルートprojectの最終責務

ルート`groundless_veryl_cores`は、最終的に製品RTLを所有しない統合projectとする。

ルートに残すもの:

- 全inner projectへのlocal path dependency
- package横断integration test
- package横断system benchmark
- 解析ツールのうち複数packageに依存するもの
- monorepo全体README、CHANGELOG、設計計画
- CIとdocumentationの入口

ルートに残さないもの:

- 公開製品module
- package内部module
- 旧namespace維持用alias
- package間の依存を隠すwrapper

## 3. 確定依存グラフ

矢印は「左の下位packageを右の上位packageが使用する」方向を表す。

```text
fixedpoint ──────┬──> interpolation ──┐
                 ├──> oscillator      │
                 ├──> delta_sigma     ├──> root integration
                 └───────────────┐    │
                                 └──> asrc ──> root integration
nco ─────────────┬──> oscillator      ↑
                 └──────────────────> asrc
filter ─────────────────────────────> asrc

uart ───────────────────────────────> midi

spi ────────────────────────────────> root integration
adat ───────────────────────────────> root integration
iec60958 ───────────────────────────> root integration
```

正確な階層は次のとおり。

```text
Level 0:
  fixedpoint
  nco
  filter
  uart
  spi
  adat
  iec60958

Level 1:
  interpolation -> fixedpoint
  oscillator    -> fixedpoint, nco
  delta_sigma   -> fixedpoint
  midi          -> uart

Level 2:
  asrc -> fixedpoint, interpolation, nco, filter

Level 3:
  groundless_veryl_cores -> all packages
```

禁止する依存:

- `nco -> oscillator`
- `interpolation -> nco`
- `interpolation -> oscillator`
- `interpolation -> asrc`
- `filter -> asrc`
- `uart -> midi`
- ADAT、IEC60958、MIDI相互のprotocol依存
- benchmarkの刺激源だけを理由にしたproduction packageからoscillatorへの依存

## 4. 共通package作成禁止と型の所有権

型は意味を所有する最下位packageに置く。

| 型・policy | 所有package |
| --- | --- |
| signed Q形式、丸め、overflow | `fixedpoint` |
| phase word、phase step、phasor | `nco` |
| 補間位置Q0.P | `interpolation`のmodule契約 |
| 波形種別 | `oscillator` |
| `SpiMode` | `spi` |
| `AdatFamily`とADAT frame型 | `adat` |
| IEC60958 sample、preamble、link type | `iec60958` |

ルートの`src/fixedpoint_aliases.veryl`は最終段階で削除する。
各packageは次のように所有namespaceを直接参照する。

```veryl
fixedpoint::Q1_31::Raw
fixedpoint::Q8_24::Raw
fixedpoint::SignedFixedPoint::convert
```

## 5. package共通構成

新規packageは原則として次を持つ。

```text
packages/<name>/
├── Veryl.toml
├── README.md
├── CHANGELOG.md
├── src/
└── tools/             # package固有ツールがある場合だけ
```

`Veryl.toml`の共通形:

```toml
[project]
name = "gndless_<name>"
version = "0.1.0"
authors = ["Akiyuki Okayasu"]
description = "<package固有の説明>"
license = "MIT OR Apache-2.0"
repository = "https://github.com/AkiyukiOkayasu/gndless-<name>-veryl"

[build]
sources = ["src"]
target = { type = "directory", path = "target" }

[test]
```

開発中の依存はlocal pathだけを使用する。
存在しないGit repositoryをdependencyへ記述してはならない。
将来repository分割するときにGit依存とlocal overrideを追加する。

各READMEに最低限記載するもの:

- packageの責務と対象外
- 公開module/package一覧
- dependency
- 入出力型、signedness、parameter範囲
- latency、clock、reset
- ready/validまたはenableの転送契約
- DSPではformat、rounding、overflow、内部gain
- protocolでは物理入力の同期化責任
- 最小使用例
- testとbuild方法

各CHANGELOGは`[Unreleased]`を持ち、初期分割内容を記録する。

## 6. package別境界とファイル移行

### 6.1 fixedpoint

既存の`packages/fixedpoint`を維持する。

公開API:

- `SignedFixedPointFormat`
- Q形式preset
- `SignedFixedPoint`
- `RoundingMode`
- `OverflowMode`
- round、resize、saturate、clamp、multiply helper

依存なし。

追加作業:

- 他packageがルートaliasではなく`fixedpoint::...`を直接使えることを確認
- package単独CIを追加
- 現行テストを減らさない

### 6.2 interpolation

作成:

```text
packages/interpolation/
├── Veryl.toml
├── README.md
├── CHANGELOG.md
├── src/
│   ├── zero_order_hold.veryl
│   ├── linear_interpolator.veryl
│   └── cubic_lagrange_interpolator.veryl
├── tools/
│   └── analyze_interpolator_benchmark.py
└── testdata/          # 必要な場合
```

抽出元:

- `src/asrc/linear_asrc.veryl`の`ZeroOrderHold`と`LinearInterpolator`
- `src/asrc/farrow_asrc.veryl`の`FarrowInterpolator`
- 対応するprimitive test
- `tools/analyze_interpolator_benchmark.py`

公開API:

- `ZeroOrderHold`
- `LinearInterpolator`
- `CubicLagrangeInterpolator`

改名:

- `FarrowInterpolator` -> `CubicLagrangeInterpolator`

依存:

```toml
[dependencies]
fixedpoint = { path = "../fixedpoint" }
```

数値APIは、既に合意した以下を実装する。

- signed sample format generic
- unsigned Q0.`PHASE_WIDTH` phase
- combinational、latency 0
- default roundingはnearest ties to even
- cubic overflowのdefaultはsaturation
- 全幅演算後に1回だけ丸め、その後overflow処理
- 4点窓は`sample_m1`, `sample0`, `sample1`, `sample2`
- cubicは4点3次Lagrangeであり、Farrow/Hornerは内部実装

`src/asrc/interpolator_benchmark.veryl`は、そのまま移さない。
現在の`SineWaveCore`依存を除き、固定vectorまたはpackage内で完結する刺激へ置換する。
production dependencyへoscillatorを追加してはならない。

### 6.3 nco

移動:

```text
src/nco/nco_tick.veryl
  -> packages/nco/src/nco_tick.veryl
src/nco/fractional_phase_accumulator.veryl
  -> packages/nco/src/fractional_phase_accumulator.veryl
src/oscillator/phasor.veryl
  -> packages/nco/src/phasor.veryl
```

公開API:

- `NcoTick`
- `ClockEnableNco`
- `FractionalPhaseAccumulator`
- `Phase`
- `Phasor`

依存なし。

`Phase`と`Phasor`はncoが所有する。これらは波形そのものではなく、
unsigned modular phaseとその進行を生成するprimitiveだからである。
oscillatorは`nco::Phase`と`nco::Phasor`を利用する。

doc commentに明記:

- accumulator width
- wrap条件
- incrementまたはmodulusの有効範囲
- `enable`停止時の保持
- restart/update/resetの優先順位
- tick/advanceのパルス幅
- phase stepの実数上の意味

### 6.4 filter

移動:

```text
src/filter/cic.veryl
  -> packages/filter/src/cic.veryl
src/filter/halfband.veryl
  -> packages/filter/src/halfband.veryl
src/filter/lpf_shift.veryl
  -> packages/filter/src/lpf_shift.veryl
src/filter/hpf_shift.veryl
  -> packages/filter/src/hpf_shift.veryl
tools/design_halfband_coefficients.py
  -> packages/filter/tools/design_halfband_coefficients.py
```

公開API:

- `CicDecimator`
- `CicInterpolator`
- `HalfbandInterpolator2x`
- `LpfShiftSigned`
- `LpfShiftVariableSigned`
- 現在存在するunsigned版
- `HpfShiftSigned`
- `HpfShiftVariableSigned`
- 現在存在するunsigned版

初回移動では外部依存なしとし、数値動作を変えない。
filter全体のformat generic化は、この分割の完了条件に含めない。
ただしREADMEには現行のraw signed/unsigned、内部gain、出力切り詰めを正確に記載する。

将来fixedpoint APIを利用する変更は別コミットにする。

### 6.5 oscillator

移動:

```text
src/oscillator/multi_wave.veryl
src/oscillator/pink_noise.veryl
src/oscillator/pwm_square.veryl
src/oscillator/saw.veryl
src/oscillator/sine.veryl
src/oscillator/sine_rom.veryl
src/oscillator/tri.veryl
src/oscillator/white_noise.veryl
```

移動先:

```text
packages/oscillator/src/
```

ツール移動:

```text
src/oscillator/sinetable/README.md
src/oscillator/sinetable/main.py
src/oscillator/sinetable/pyproject.toml
src/oscillator/sinetable/uv.lock
src/oscillator/sinetable/.python-version
src/oscillator/sinetable/sine_data.txt
  -> packages/oscillator/tools/sinetable/
```

`.venv`は移動せず、Git管理対象にしない。

公開API:

- `SineWaveCore`
- `SineWaveLerpCore`
- `SineOscillator`
- `SineOscillatorLerp`
- `TriangleWaveCore`
- `TriangleOscillator`
- `SawWaveCore`
- `SawOscillator`
- `SquareWaveCore`
- `PwmSquareOscillator`
- `MultiWaveCore`
- `MultiWaveOscillator`
- `WhiteNoise`
- `PinkNoise`
- 波形種別package/enum

内部API:

- `SineRomQuarter`
- `SineRomQuarterDual`

依存:

```toml
[dependencies]
fixedpoint = { path = "../fixedpoint" }
nco = { path = "../nco" }
```

変更:

- `Phasor` -> `nco::Phasor`
- `Phase` -> `nco::Phase`
- `Q1_31`、`Q8_24`等 -> `fixedpoint::...`
- `SignedFixedPoint`、`FixedPoint` -> `fixedpoint::...`

初回移動では波形アルゴリズム、ROM値、振幅formatを変更しない。

### 6.6 asrc

移動・再構成:

```text
src/asrc/linear_asrc.veryl
  -> packages/asrc/src/linear_asrc.veryl
src/asrc/farrow_asrc.veryl
  -> packages/asrc/src/cubic_lagrange_asrc.veryl
src/asrc/four_x_halfband_asrc.veryl
  -> packages/asrc/src/four_x_halfband_asrc.veryl
src/asrc/sample_rate_tracker.veryl
  -> packages/asrc/src/sample_rate_tracker.veryl
```

公開API:

- `LinearAsrc`
- `ContinuousLinearAsrc`
- `CubicLagrangeAsrc`
- `FourXHalfbandAsrc`
- `SampleRateTracker`

改名:

- `FarrowAsrc` -> `CubicLagrangeAsrc`

依存:

```toml
[dependencies]
fixedpoint = { path = "../fixedpoint" }
interpolation = { path = "../interpolation" }
nco = { path = "../nco" }
filter = { path = "../filter" }
```

変更:

- primitive定義とprimitive testをASRCファイルから削除
- `LinearInterpolator` -> `interpolation::LinearInterpolator`
- `FarrowInterpolator` -> `interpolation::CubicLagrangeInterpolator`
- `FractionalPhaseAccumulator` -> `nco::FractionalPhaseAccumulator`
- `HalfbandInterpolator2x` -> `filter::HalfbandInterpolator2x`
- ASRC固有のFIFO/window/refill/timing testだけを残す

`src/asrc/fixed_rate_asrc_benchmark.veryl`はASRC packageへ移さない。
oscillatorを含むため、ルート統合projectへ置く。

### 6.7 delta_sigma

移動:

```text
src/delta_sigma/delta_sigma.veryl
  -> packages/delta_sigma/src/delta_sigma.veryl
```

公開API:

- `DeltaSigma1st`
- `DeltaSigma2nd`

依存:

```toml
[dependencies]
fixedpoint = { path = "../fixedpoint" }
```

変更:

- `Q1_31` -> `fixedpoint::Q1_31`

初版はQ1.31専用契約を維持してよい。分割と同時に無理にformat generic化しない。

### 6.8 uart

移動:

```text
src/uart/uart_rx.veryl
  -> packages/uart/src/uart_rx.veryl
```

公開API:

- `UartRx`

依存なし。

公開契約を明記:

- clock frequency
- baud rate
- frame形式
- data width
- 入力同期化の責任
- `valid`のパルス幅
- framing errorの現行動作

重要: 現行回路を確認して、UARTとMIDIの両方で不要な二重同期化を増やさない。
分割時にCDC回路を変更する場合は、専用テストと別コミットが必要である。

### 6.9 midi

移動:

```text
src/midi/midi_rx.veryl
  -> packages/midi/src/midi_rx.veryl
```

公開API:

- `MidiRx`

依存:

```toml
[dependencies]
uart = { path = "../uart" }
```

変更:

- `UartRx` -> `uart::UartRx`
- baud rateはMIDI規格の31,250へ固定
- 公開parameterはsystem clock等、本当に利用者が変更するものだけにする

`MidiRx`はMIDI message parserではなく、MIDI速度のbyte receiverであることを明記する。

### 6.10 spi

移動:

```text
src/spi/spi_types.veryl
  -> packages/spi/src/spi_types.veryl
src/spi/spi_master.veryl
  -> packages/spi/src/spi_master.veryl
```

公開API:

- `SpiMode`
- `SpiMaster`

依存なし。

breaking changeを許容するため、以下を今回実施する。

- `spi_pkg` -> `Spi`
- `spi_pkg::SpiMode` -> `Spi::SpiMode`

consumerからはdependency namespaceを含めて`spi::Spi::SpiMode`となる。
Verylがdependency rootへの直接re-exportを提供していない場合、無理に
`spi::SpiMode`を実現するalias層は追加しない。

### 6.11 adat

移動:

```text
src/adat/*
  -> packages/adat/src/*
```

公開API:

- `Adat`
- `AdatRx`
- `AdatTx`
- `Smux2Packer`
- `Smux2Unpacker`

内部APIのまま維持:

- `TimingTracker`
- `BitDecoder`
- `FrameParser`
- `OutputInterface`
- `TxFrameBuilder`
- `TxBitSerializer`
- `TxNrziEncoder`

依存はVeryl stdのみ。
内部moduleを移動の都合で`pub`へ変更してはならない。

### 6.12 iec60958

移動:

```text
src/iec60958/*
  -> packages/iec60958/src/*
```

公開API:

- `Iec60958`
- `Spdif`
- `Aes3`
- `SpdifTransmitter`
- `SpdifReceiver`
- `Aes3Transmitter`
- `Aes3Receiver`

内部API:

- BMC serializer/deserializer
- subframe packer/unpacker
- block scheduler
- stereo Tx/Rx
- CRC
- channel-status stream

依存はVeryl stdのみ。
S/PDIF、AES3、共通codecは同じ規格契約を共有するため分けない。

### 6.13 root integration

最終構成:

```text
src/
└── integration/
    └── fixed_rate_asrc_benchmark.veryl
```

移動:

```text
src/asrc/fixed_rate_asrc_benchmark.veryl
  -> src/integration/fixed_rate_asrc_benchmark.veryl
```

参照をqualified nameへ変更:

```veryl
nco::FractionalPhaseAccumulator
oscillator::SineWaveCore
asrc::ContinuousLinearAsrc
asrc::FourXHalfbandAsrc
```

ルートに残す解析:

```text
tools/analyze_fixed_rate_asrc.py
```

削除:

```text
src/fixedpoint_aliases.veryl
空になった旧src/adat/
空になった旧src/asrc/
空になった旧src/delta_sigma/
空になった旧src/filter/
空になった旧src/iec60958/
空になった旧src/midi/
空になった旧src/nco/
空になった旧src/oscillator/
空になった旧src/spi/
空になった旧src/uart/
```

互換aliasやwrapperは残さない。

ルート`Veryl.toml`の最終dependency:

```toml
[dependencies]
fixedpoint = { path = "./packages/fixedpoint" }
interpolation = { path = "./packages/interpolation" }
nco = { path = "./packages/nco" }
filter = { path = "./packages/filter" }
oscillator = { path = "./packages/oscillator" }
asrc = { path = "./packages/asrc" }
delta_sigma = { path = "./packages/delta_sigma" }
uart = { path = "./packages/uart" }
midi = { path = "./packages/midi" }
spi = { path = "./packages/spi" }
adat = { path = "./packages/adat" }
iec60958 = { path = "./packages/iec60958" }
```

## 7. 実装順序

一気に実装してよいが、全packageを移動してから初めてtestすることは禁止する。
依存階層ごとに成立させ、各checkpointで失敗を解消してから次へ進む。

### Phase 0: baseline固定

変更前にルートで実行:

```text
veryl migrate --check
veryl fmt --check
veryl check
veryl test
veryl test --backend-validate
veryl build
veryl doc
veryl test --ignored -t interpolator_benchmark
veryl test --ignored -t fixed_rate_asrc_benchmark
python3 tools/analyze_interpolator_benchmark.py target/interpolator_benchmark.csv --format json
python3 tools/analyze_fixed_rate_asrc.py target/fixed_rate_asrc_benchmark.csv
```

保存・記録:

- test件数とtest名
- benchmark CSV
- interpolation解析JSONとfixed-rate ASRC解析出力
- `rg '^pub (module|package)' src`
- 生成SystemVerilog module/package一覧
- `git status --short`

baselineが失敗した場合:

- package分割を開始しない
- 既存不具合かtoolchain差かを記録
- 必要ならbaseline修正だけを独立コミットにする

### Phase 1: Level 0 leaf package

順序:

1. existing fixedpointの単独検証
2. nco
3. filter
4. uart
5. spi
6. adat
7. iec60958

各package作成直後に、そのpackage内で次を実行:

```text
veryl fmt
veryl fmt --check
veryl check
veryl test
veryl build
veryl doc
```

Level 0全完了後、ルートに一時的なpath dependencyを追加して`veryl check`する。
互換aliasは追加しない。

### Phase 2: Level 1 package

順序:

1. interpolation
2. oscillator
3. delta_sigma
4. midi

interpolationは、移動前characterization testを確保した後に数値APIを変更する。
数値API変更前後のgolden差を別に記録する。

各packageでLevel 0と同じ検証を行う。

### Phase 3: ASRC

1. ASRC moduleから補間primitiveを除去
2. dependencyをqualified nameへ変更
3. `FarrowAsrc`を`CubicLagrangeAsrc`へ改名
4. primitive testを削除し、ASRC統合testは維持
5. package単独検証
6. ignoredではないASRC testを全実行

### Phase 4: root integration

1. 全path dependencyを登録
2. system benchmarkを`src/integration`へ移動
3. 全参照をqualified nameへ変更
4. `fixedpoint_aliases.veryl`を削除
5. 旧sourceの重複を検索して削除
6. Verylによってルートと各packageのlockを生成
7. README、AUDIO_PIPELINE_PLAN、CHANGELOGを更新

### Phase 5: CIとdocumentation

1. package matrixを追加
2. root integration jobを追加
3. backend validation jobを追加
4. numerical smoke jobを追加
5. Pagesのpath対象に`packages/**`を追加
6. 各packageのdoc生成を確認

### Phase 6: final regression

全packageをLevel順に再検証し、最後にルート統合検証とbenchmarkを実行する。

## 8. package別必須テスト

既存testは所有packageへ移し、意図的統合以外で減らしてはならない。

### fixedpoint

- 全rounding mode
- 全overflow mode
- signed MIN/MAX
- format拡張・縮小
- 小数bit増減
- saturation、clamp
- preset width/fractionのstatic確認

### interpolation

- ZOHのMIN/MAX/0/正負bit完全一致
- linearのphase 0、中点、最大phase
- 上昇、下降、符号跨ぎ、同値入力
- sample width 4、phase width 3の2,048ケース全探索
- 正負tieと全rounding mode
- cubicの定数列、一次ramp、basis impulse
- cubicの正負overshoot、saturation、wrap
- 高精度referenceとbit-accurate reference
- 係数量子化誤差bound

### nco

- phase wrap直前、wrap時、wrap直後
- increment 0、1、最大有効値
- enable停止中の状態保持
- reset/restart/update優先順位
- tick/advanceが1 cycle pulse
- 長期間の平均tick/advance数
- parameter最小幅

### filter

- CIC DC gain
- CIC decimation/interpolation周期
- accumulator境界
- halfband impulse response
- halfband stream valid/readyまたはenable
- LPF/HPF step response
- signed正負対称性
- unsigned境界
- stall中の状態保持
- reset後の既定出力

### oscillator

- phaseの0、1/4、1/2、3/4周期
- sine ROM境界と象限接続
- lerp有無の既知値
- saw/triangle/squareの振幅範囲
- duty 0、50%、最大
- multi-wave選択
- white/pink noiseの状態進行
- noiseの短期goldenと長期統計を分離
- ROM生成結果とchecked-in dataの一致

### asrc

- FIFO empty/full
- 同時push/pop
- sample window初期化
- advance 0～4
- refill 1～4
- output tick停止・再開
- integer/fraction ratio
- underflow sticky
- startup level境界
- negative、MIN/MAX sample
- linear/cubic/4x halfbandの統合
- interpolation API変更後の承認済みgolden

### delta_sigma

- 0入力のdensity
- 正負入力のdensity
- 正負対称性
- MIN/MAX
- 1次/2次の長時間安定性
- resetとenableの状態
- outputが常に1bit
- idle patternの短期golden

### uart

- 0x00、0xff、代表byte
- 全256 byteまたは妥当な全探索
- 連続frame
- start/stop bit境界
- baud divisor境界
- baud timing誤差の許容範囲
- reset途中
- 入力同期化契約に対応したtest

### midi

- 31,250 baud
- 連続byte
- 0x00、0xff、status/data代表値
- UART validの伝播
- synchronizerによる一定latency
- MIDI message解析を行わないこと

### spi

- Mode 0～3
- idle polarity
- sampling edge
- 複数data width
- 連続transaction
- start受付条件
- busy/done
- CS setup/hold
- CLK_DIV最小値と奇数値
- MISO同期化

### adat

- TimingTracker
- BitDecoder
- FrameParser
- TxFrameBuilder
- TxNrziEncoder
- TxBitSerializer
- OutputInterface
- Tx/Rx loopback
- sync獲得、喪失、再獲得
- 8channel frame
- 44.1k/48k family
- S/MUX2 pack/unpack mapping

### iec60958

- BMC golden
- preamble normal/inverted
- subframe pack/unpack
- parity
- block scheduler
- stereo Tx/Rx loopback
- S/PDIF link loopback
- AES3 link loopback
- channel status
- CRC
- sample rate code

### root integration

- fixed-rate ASRC benchmark smoke
- oscillator -> ASRC横断接続
- benchmark CSV schema
- Python解析成功
- underflow 0
- 承認済み振幅・誤差閾値

## 9. benchmark配置

### interpolation package

補間カーネルだけを評価する。

- oscillatorへ依存しない
- deterministic input vectorを使用
- ideal referenceと量子化referenceを分ける
- PRでは短縮smoke
- mainまたは定期実行では完全評価

### root integration

以下を含む`fixed_rate_asrc_benchmark`を置く。

- oscillator
- nco
- interpolation
- filter
- asrc

`tools/analyze_fixed_rate_asrc.py`もルートに残す。

## 10. CI計画

### package-fast matrix

対象:

```text
packages/fixedpoint
packages/nco
packages/filter
packages/uart
packages/spi
packages/adat
packages/iec60958
packages/interpolation
packages/oscillator
packages/delta_sigma
packages/midi
packages/asrc
```

各working directoryで実行:

```text
veryl fmt --check
veryl check
veryl build
veryl test
```

### backend-validation

可能なら全packageで実行する。
時間が問題になる場合でも最低限次を対象にする。

```text
packages/fixedpoint
packages/interpolation
packages/nco
packages/filter
packages/asrc
packages/uart
packages/spi
packages/adat
packages/iec60958
.
```

### root-integration

```text
veryl fmt --check
veryl check
veryl build
veryl test
veryl test --backend-validate
```

### numerical-smoke

PR:

- interpolation短縮benchmark
- fixed-rate ASRC短縮benchmark
- Python解析
- JSON閾値判定

mainまたは定期実行:

- full ignored benchmark
- 全周波数
- 長時間平均
- baseline比較

### docs

- 各packageで`veryl doc`
- Pages workflowのpath対象へ以下を追加

```text
packages/**/*.veryl
packages/**/Veryl.toml
packages/**/README.md
```

## 11. commit方針

作業は一気に進めてよいが、一つの巨大commitにしない。

推奨commit順:

1. `test: package分割前の回帰基準を強化`
2. `BREAKING CHANGE: NCOを独立Veryl projectへ分割`
3. `BREAKING CHANGE: filterを独立Veryl projectへ分割`
4. `BREAKING CHANGE: UARTとMIDIを独立Veryl projectへ分割`
5. `BREAKING CHANGE: SPIを独立Veryl projectへ分割`
6. `BREAKING CHANGE: ADATを独立Veryl projectへ分割`
7. `BREAKING CHANGE: IEC60958を独立Veryl projectへ分割`
8. `BREAKING CHANGE: 補間primitiveを独立Veryl projectへ分割`
9. `BREAKING CHANGE: 補間の数値APIを明確化`
10. `BREAKING CHANGE: oscillatorを独立Veryl projectへ分割`
11. `BREAKING CHANGE: delta-sigmaを独立Veryl projectへ分割`
12. `BREAKING CHANGE: ASRCを独立Veryl projectへ分割`
13. `refactor: ルートを統合projectへ整理`
14. `ci: 全inner projectを個別検証`
15. `docs: package構成と利用方法を更新`

数値変更は移動commitと分ける。
各commit時点で少なくとも変更対象packageと、その直接利用側がbuild/test可能であること。

## 12. 停止条件

次の場合は無理に先へ進まず、原因を記録して停止する。

- baselineの既存testが失敗する
- package単独で`veryl check`できず、上位packageへの逆依存が必要になる
- 循環依存が必要になる
- testを通すために非公開moduleを不用意に`pub`へ変える必要がある
- 数値結果が変化したがreferenceまたは仕様で説明できない
- generated RTLで同名moduleが二重生成される
- lock fileに同一projectの意図しない複数revisionが現れる
- Veryl更新によるmigrationがpackage分割と混ざり、差分を判別できない
- CDC責務変更を既存testだけで検証できない

停止時は、直前の成立checkpoint、失敗command、最小再現、変更差分を報告する。

## 13. 最終受入条件

### 構造

- 全製品moduleがちょうど一つのinner projectに所属する
- ルート`src/`には統合test/benchmark以外の公開RTLがない
- `src/fixedpoint_aliases.veryl`が削除されている
- 旧sourceと新packageに重複定義がない
- 全packageに`Veryl.toml`、README、CHANGELOGがある

### 依存

- 依存グラフが本計画どおりのDAG
- 下位packageが上位packageを参照しない
- production packageにbenchmark専用依存がない
- protocol package間に依存がない
- ルートaliasで依存が隠されていない

### API

- `FarrowInterpolator`が`CubicLagrangeInterpolator`へ移行
- `FarrowAsrc`が`CubicLagrangeAsrc`へ移行
- `Phase`と`Phasor`をncoが所有
- `spi_pkg`が`Spi`へ移行
- 公開moduleに日本語doc commentがある
- parameter、port、latency、reset、protocol、formatが説明されている

### 生成RTL

- project prefixが`gndless_*`へ分離されている
- `omit_project_prefix`を使用していない
- 旧`groundless_veryl_cores_*`の製品moduleが残っていない
- file listに各moduleが一度だけ含まれる

### 検証

全package:

```text
veryl fmt --check
veryl check
veryl test
veryl build
veryl doc
```

重要packageとルート:

```text
veryl test --backend-validate
```

ルート:

```text
veryl test --ignored -t fixed_rate_asrc_benchmark
python3 tools/analyze_fixed_rate_asrc.py target/fixed_rate_asrc_benchmark.csv
```

### リグレッション

- 既存Native testが意図せず減っていない
- 数値変更以外はbaselineとbit exact
- 補間の数値変更は承認済みgoldenと一致
- benchmark差が仕様で説明されている
- clean checkoutから全projectをbuildできる
- `git diff --check`が成功
- `target/`、`doc/`、`dependencies/`を直接編集していない
- 不要な生成物や仮想環境を追加していない
- rootと各packageの`[Unreleased]`が更新されている

## 14. repository分割時の将来手順

今回実施しない。

APIが安定した後、依存のtopological orderでrepository化・publishする。

第1群:

```text
fixedpoint
nco
filter
uart
spi
adat
iec60958
```

第2群:

```text
interpolation
oscillator
delta_sigma
midi
```

第3群:

```text
asrc
```

repository分割後の依存例:

```toml
fixedpoint = {
    project = "gndless_fixedpoint",
    github = "AkiyukiOkayasu/gndless-fixedpoint-veryl",
    version = "0.1.0",
    path = "../fixedpoint"
}
```

publish時は次を守る。

1. `Veryl.toml`のversion変更だけをcommit
2. `veryl publish`
3. 生成された`Veryl.pub`だけを別commit

ルート`groundless_veryl_cores`はregistry packageとして公開せず、統合開発repositoryとして
残す。互換bundleへの明確な需要が出た場合だけmeta packageを別途検討する。
