# Changelog

## [Unreleased]

- 各testのdoc commentへ検証対象を明記
### Changed

- CIC、halfband、LPF、HPFを独立packageへ移動
- halfband固有の幅変換adapterを削除し、fixedpointのproject-scope `resize`を使用
- halfbandのready/valid burstとCICの入出力周期を示すWavedromを追加
