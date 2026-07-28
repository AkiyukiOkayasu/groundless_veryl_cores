# Changelog

## [Unreleased]

- 公開moduleのparam/port doc commentを宣言末尾へ統一し、ADAT説明文の改行を整理
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary、箇条書き、`Examples`見出し、code fence形式を整理
- 各testへ検証目的を示すdoc commentを追加
- 公開型packageをproject名と重複する`Adat`から`Types`へ改名
### Changed

- ADAT RX/TXとS/MUX2を独立packageへ移動
- 内部送信helperを`FrameBuilder`、`BitSerializer`、`NrziEncoder`へ改名
- `adat_rx.veryl`に集中していたunit testを各helperの実装ファイルへ移動
- `AdatRx`は50MHzでのみ実機確認済み、`AdatTx`は実機未確認であることをREADMEとmodule docへ明記
- `AdatRx`のmodule docを公開信号の契約に絞り、NRZI復号後の詳細frame図をREADMEへ移動
- `AdatTx`のWavedromを公開信号の契約へ整理し、S/MUX2 pack/unpackの時間順序図を追加
- `AdatRx`のS/MUX2受信案内を`Smux2Unpacker`へ明確化
