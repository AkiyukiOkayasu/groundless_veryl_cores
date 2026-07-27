# Groundless Electronics Veryl RTL core

[![Documentation](https://github.com/AkiyukiOkayasu/groundless_veryl_cores/actions/workflows/pages.yml/badge.svg)](https://akiyukiokayasu.github.io/groundless_veryl_cores/)

Verylで記述した、オーディオ信号処理・デジタルオーディオ伝送向けのRTLコア集です。
各コアは単体で利用できる公開モジュールと、Veryl Native testによる回帰テストを持ちます。

## package構成

| package | 主な公開API | 用途 |
| --- | --- | --- |
| `fixedpoint` | `SignedFixedPoint`, Q形式preset | signed固定小数点演算 |
| `interpolation` | `ZeroOrderHold`, `LinearInterpolator`, `CubicLagrangeInterpolator` | 組み合わせ補間kernel |
| `nco` | `NcoTick`, `FractionalPhaseAccumulator`, `Phase`, `Phasor` | phaseとclock-enable生成 |
| `filter` | CIC、halfband、LPF/HPF | レート変換とaudio filter |
| `oscillator` | sine/triangle/saw/square/noise | 波形・ノイズ生成 |
| `asrc` | `LinearAsrc`, `CubicLagrangeAsrc`, `FourXHalfbandAsrc` | 分数比sample-rate conversion |
| `delta_sigma` | `DeltaSigma1st`, `DeltaSigma2nd` | Q1.31 PCMからPDM生成 |
| `uart` / `midi` | `UartRx`, `MidiRx` | UARTとMIDI速度byte受信 |
| `spi` | `Spi::SpiMode`, `SpiMaster` | SPI master |
| `adat` | `AdatRx`, `AdatTx`, `Smux2*` | 8ch ADATとS/MUX2 |
| `iec60958` | S/PDIF/AES3 transceiver | IEC 60958 link |

各packageは`packages/<name>/`の独立Veryl projectです。依存方向はleafから上位へ一方向で、
rootはpackage横断benchmarkとintegration testだけを所有します。各packageの責務、型、
signedness、latency、reset、転送契約は対応するREADMEとdoc commentに記載しています。

当面のADAT→50MHz差動PDMと将来のI2S出力の実装計画は、[AUDIO_PIPELINE_PLAN.md](AUDIO_PIPELINE_PLAN.md)にまとめています。

詳細なポート一覧と型は、[公開ドキュメント](https://akiyukiokayasu.github.io/groundless_veryl_cores/)を参照してください。

固定小数点演算は`packages/fixedpoint/`の`gndless_fixedpoint`として管理し、
他packageからは`fixedpoint::...`で直接参照します。全packageは当面monorepo内の
local path dependencyだけを使用し、外部repository化とregistry publishは行いません。

## インターフェース方針

- 設計上0/1だけを保証でき、true/falseで表現でき、かつ`bbool`にすることで意図の可読性が高まる1bit値は`bbool`を使用します（例: `enable`、`invalid`、`locked`、`error`）。
- `valid`/`ready`やイベントパルスも、真偽値として読む方が自然で2値保証できるなら`bbool`の対象です。逆に、生のビット列・波形・プロトコル線として読む値は、0/1しか現れなくても`logic`で保持します。
- 真偽値として扱うが`x/z`を保持・伝播したい値には`lbool`を使用します。
- 物理線、クロック、シリアルbit、プロトコルpayload bitは`logic`で保持します。
- システムクロックとシステムリセットは、それぞれ`clock`と`reset`を使用します。
- ポート名は方向接頭辞を付けないsemantic nameに統一しています。

ADATの`FrameParser`は内部カウンタ上のチャンネル終了位置を生成ループで判定し、
`TxFrameBuilder`は8チャンネルの30bit符号化を生成配列へまとめてフレームを構築します。
両方とも8チャンネルを対象にしたNative testで回帰を検証しています。

IEC60958では、共通codecの上にS/PDIFとAES3の公開ラッパーを配置しています。
`SpdifReceiver`と`Aes3Receiver`は利用者向けAPIとして維持しています。

## 検証

RTL編集後は次の順序で検証します。

```text
veryl fmt --check
veryl check
veryl test
veryl build
veryl doc
```

生成RTLとNative backendの確認には、さらに次を実行します。

```text
veryl test --backend-validate
veryl doc
```

補間方式の定量比較は、まずNative testでCSVを生成し、その後に依存パッケージなしの解析スクリプトを実行します。

```text
cd packages/interpolation
veryl test --ignored -t interpolator_benchmark
python3 tools/analyze_interpolator_benchmark.py target/interpolator_benchmark.csv
```

実レート比の比較では、ignoredのVeryl Native testで1kHz／10kHz／18kHz／20kHzのCSVを生成し、
直接線形補間と4倍HBF＋線形補間の振幅を標準Pythonだけで解析します。

```text
cd ../..
veryl test --ignored -t fixed_rate_asrc_benchmark
python3 tools/analyze_fixed_rate_asrc.py target/fixed_rate_asrc_benchmark.csv
```

`--format json`を付けると、CIや別の数値解析へ渡しやすいJSONになります。

Verylのgeneric引数可視性制約とfixedpointのAPI設計理由は、
[`packages/interpolation/README.md`](packages/interpolation/README.md)と
[fixedpointのREADME](packages/fixedpoint/README.md)、
[Veryl #3110](https://github.com/veryl-lang/veryl/issues/3110)に記録しています。
