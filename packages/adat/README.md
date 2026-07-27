# gndless_adat

ADAT opticalの8ch受信・送信とS/MUX2 pack/unpackを所有します。公開APIは`Adat`、`AdatRx`、`AdatTx`、`Smux2Packer`、`Smux2Unpacker`です。内部tracker、decoder、parser、serializerは公開しません。

依存はVeryl stdのみです。`AdatFamily`は44.1kHz/48kHz family、frameは8ch・30bit符号化です。物理入力の同期化責任は利用者にあり、RXのsync獲得・喪失・再獲得、TXのbit/NRZI順序、S/MUX2 mappingはmodule doc commentとNative testで定義します。clock/resetは同期です。

```veryl
inst rx: adat::AdatRx (...);
inst tx: adat::AdatTx (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
