# Changelog

## [Unreleased]

- 公開transceiverのport doc commentを追加し、説明文を日本語と単一行段落へ整理
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary表記を統一
- 各testのdoc commentを検証目的が分かる表現へ統一

### Changed

- IEC60958共通型packageをproject名と重複する`Iec60958`から`Types`へ改名
- 公開transceiverへstereo sample handshake、A/B subframe、RX backpressureのWavedromを追加

- IEC60958共通codec、S/PDIF、AES3を独立packageへ移動
