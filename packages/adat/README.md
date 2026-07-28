# gndless_adat

ADAT opticalの8ch受信・送信とS/MUX2 pack/unpackを所有します。公開APIは`Adat`、`AdatRx`、`AdatTx`、`Smux2Packer`、`Smux2Unpacker`です。内部tracker、decoder、parser、serializerは公開しません。

依存はVeryl stdのみです。`AdatFamily`は44.1kHz/48kHz family、frameは8ch・30bit符号化です。物理入力の同期化責任は利用者にあり、RXのsync獲得・喪失・再獲得、TXのbit/NRZI順序、S/MUX2 mappingはmodule doc commentとNative testで定義します。clock/resetは同期です。

## 実機確認状況

- `AdatRx`はシステムクロック50MHzの構成で実機動作を確認済みです。50MHz以外のシステムクロックでは実機確認していません。
- `AdatTx`は実機動作未確認です。現時点の確認範囲はNative testと、RTL内部で接続した`AdatTx`→`AdatRx` loopback testです。外部ADAT機器との相互接続、光送信回路を含む電気的条件、実機上のタイミングは未検証です。

```veryl
inst rx: adat::AdatRx (...);
inst tx: adat::AdatTx (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
