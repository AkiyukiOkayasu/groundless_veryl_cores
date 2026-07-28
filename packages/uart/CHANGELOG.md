# Changelog

## [Unreleased]

- 公開moduleのparam/port doc commentを追加し、説明文の途中改行を整理
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary表記を統一
- UART受信testのdoc commentへ検証対象を明記
### Changed

- UART receiverを独立packageへ移動
- `UartRx`へLSB-first frame、中央sampling、`valid`のWavedromを追加
