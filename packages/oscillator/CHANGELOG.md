# Changelog

## [Unreleased]

- 各testのdoc commentを検証目的が分かる表現へ統一
### Changed

- waveform/noise oscillatorを独立packageへ移動
- phase primitiveを`nco` packageへ移し、依存namespaceを明示
- fixedpoint format変換をflatなproject-scope `convert` APIへ移行
