# Changelog

## [Unreleased]

- 公開moduleのparam/port doc commentを追加し、MIDI入力コメントをdoc commentへ統一
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary表記を統一
- MIDI受信testへ検証目的を示すdoc commentを追加
### Changed

- MIDI byte receiverをUART依存の独立packageへ移動
- UART frame timingは`UartRx`のWavedromを参照することをmodule documentationへ明記
