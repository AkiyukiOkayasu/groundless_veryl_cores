# gndless_adat

ADAT opticalの8ch受信・送信とS/MUX2 pack/unpackを所有します。公開APIは`Adat`、`AdatRx`、`AdatTx`、`Smux2Packer`、`Smux2Unpacker`です。内部tracker、decoder、parser、serializerは公開しません。

依存はVeryl stdのみです。`AdatFamily`は44.1kHz/48kHz family、frameは8ch・30bit符号化です。物理入力の同期化責任は利用者にあり、RXのsync獲得・喪失・再獲得、TXのbit/NRZI順序、S/MUX2 mappingはmodule doc commentとNative testで定義します。clock/resetは同期です。

## 実機確認状況

- `AdatRx`はシステムクロック50MHzの構成で実機動作を確認済みです。50MHz以外のシステムクロックでは実機確認していません。
- `AdatTx`は実機動作未確認です。現時点の確認範囲はNative testと、RTL内部で接続した`AdatTx`→`AdatRx` loopback testです。外部ADAT機器との相互接続、光送信回路を含む電気的条件、実機上のタイミングは未検証です。

## ADATフレーム構造

以下の図は、物理入力`adat`をNRZI復号した後の256bit論理フレームを示します。電気的なNRZI波形ではありません。シリアル伝送位置0から255へ進むとき、内部ベクタは`frame[255]`から`frame[0]`へ進みます。

```text
伝送位置    0          10 11       15 16                  45             226                255
             |           | |         | |                    |               |                  |
伝送順  →  +-------------+-----------+----------------------+----- ... -----+------------------+
            | SYNC        | User      | CH0                  |               | CH7              |
            | 10bit + sep | 4bit+sep  | 6 * (4bit + sep)    |    CH1-CH6    | 6*(4bit + sep)  |
           +-------------+-----------+----------------------+----- ... -----+------------------+
vector      [255:245]      [244:240]   [239:210]                              [29:0]
bit数           11             5           30                    180             30
```

| 伝送位置 | 内部ベクタ | 内容 |
|---:|:---:|---|
| 0–9 | `frame[255:246]` | SYNCの0を10bit |
| 10 | `frame[245]` | SYNC separator = 1 |
| 11–14 | `frame[244:241]` | User bit U3→U0 |
| 15 | `frame[240]` | User separator = 1 |
| 16–45 | `frame[239:210]` | CH0 |
| 46–75 | `frame[209:180]` | CH1 |
| 76–105 | `frame[179:150]` | CH2 |
| 106–135 | `frame[149:120]` | CH3 |
| 136–165 | `frame[119:90]` | CH4 |
| 166–195 | `frame[89:60]` | CH5 |
| 196–225 | `frame[59:30]` | CH6 |
| 226–255 | `frame[29:0]` | CH7 |

各channelは24bit PCMをMSB-firstで6個のnibbleに分け、各4bitの後ろにseparator=1を置きます。

```text
channel内の伝送順 →
+-------------+-------------+-------------+-------------+-------------+-------------+
| D23..D20  1 | D19..D16  1 | D15..D12  1 | D11..D8   1 | D7..D4    1 | D3..D0    1 |
+-------------+-------------+-------------+-------------+-------------+-------------+
    nibble 0      nibble 1      nibble 2      nibble 3      nibble 4      nibble 5
```

SYNC以外ではseparatorによってNRZI信号に5bitごとの遷移が生じ、clock recoveryに必要な同期機会が保たれます。SYNCの10bit連続0は、フレーム境界を検出するための意図的な無遷移区間です。`channels[0]`から`channels[7]`はADATの物理スロットです。S/MUX2/S/MUX4での論理channel再構成は`Smux2Packer`、`Smux2Unpacker`または利用側の回路で行います。

```veryl
inst rx: adat::AdatRx (...);
inst tx: adat::AdatTx (...);
```

検証: `veryl fmt && veryl check && veryl test && veryl build && veryl doc`。
