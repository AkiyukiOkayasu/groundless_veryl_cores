# Groundless Electronics Veryl RTL core

[![Documentation](https://github.com/AkiyukiOkayasu/groundless_veryl_cores/actions/workflows/pages.yml/badge.svg)](https://github.com/AkiyukiOkayasu/groundless_veryl_cores/actions/workflows/pages.yml)

Verylで記述した、オーディオ信号処理・デジタルオーディオ伝送向けのRTLコア集です。
各コアは単体で利用できる公開モジュールと、Veryl Native testによる回帰テストを持ちます。

## モジュール構成

| 領域 | 主なモジュール | 用途 |
| --- | --- | --- |
| ADAT | `AdatRx`, `AdatTx` | 8ch ADAT受信・送信、S/MUX2パッキング |
| IEC60958 | `SpdifTransmitter`/`SpdifReceiver`, `Aes3Transmitter`/`Aes3Receiver` | S/PDIF・AES3のstereo transceiver |
| ASRC | `LinearAsrc`, `FarrowAsrc` | 分数比サンプルレート変換 |
| 固定小数点・変調 | `FixedPoint`, `DeltaSigma1st`, `DeltaSigma2nd` | PCM演算とPDM生成 |
| フィルタ・発振器 | `LpfShift*`, `HpfShift*`, 各wave core | オーディオ信号処理 |
| 周辺I/O | `SpiMaster`, `UartRx`, `MidiRx` | シリアルインターフェース |

詳細なポート一覧と型は、[公開ドキュメント](https://akiyukiokayasu.github.io/groundless_veryl_cores/)を参照してください。

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
veryl fmt
veryl check
veryl test
```

生成RTLとNative backendの確認には、さらに次を実行します。

```text
veryl build --check
veryl test --backend-validate
veryl doc
```
