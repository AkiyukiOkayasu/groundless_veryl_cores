# Changelog

## [Unreleased]

- 公開moduleのparam/port doc commentを追加し、説明文の途中改行を整理
- doc commentの句点と体言止めの表記を整理
- doc commentのsummary表記を統一
- 各testのdoc commentへ検証対象を明記
### Changed

- CIC、halfband、LPF、HPFを独立packageへ移動
- halfband固有の幅変換adapterを削除し、fixedpointのproject-scope `resize`を使用
- halfbandのready/valid burstとCICの入出力周期を示すWavedromを追加
