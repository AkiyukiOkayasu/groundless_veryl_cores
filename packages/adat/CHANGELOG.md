# Changelog

## [Unreleased]

### Changed

- ADAT RX/TXとS/MUX2を独立packageへ移動
- 内部送信helperを`FrameBuilder`、`BitSerializer`、`NrziEncoder`へ改名
- `adat_rx.veryl`に集中していたunit testを各helperの実装ファイルへ移動
- `AdatRx`は50MHzでのみ実機確認済み、`AdatTx`は実機未確認であることをREADMEとmodule docへ明記
