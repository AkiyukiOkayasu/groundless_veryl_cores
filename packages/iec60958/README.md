# gndless_iec60958

IEC 60958共通codecの上にS/PDIFとAES3のlink transceiverを提供します。公開APIは`Iec60958`、`Spdif`、`Aes3`、`SpdifTransmitter`、`SpdifReceiver`、`Aes3Transmitter`、`Aes3Receiver`です。

依存はVeryl stdのみです。sampleはIEC60958のpayload型、preamble・parity・192-frame block scheduler・channel status・AES3 CRCを共通契約で扱います。BMC serializer、subframe、stereo I/O、status streamは内部APIです。物理linkの同期化責任は利用者にあり、公開transceiverのlatencyとreset契約は各module doc commentに記載します。

```veryl
inst tx: iec60958::SpdifTransmitter (...);
inst rx: iec60958::Aes3Receiver (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
