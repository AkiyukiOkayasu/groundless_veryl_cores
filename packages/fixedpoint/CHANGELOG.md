# Changelog

このプロジェクトの注目すべき変更を記録します。

## [Unreleased]

## [0.1.0] - 2026-07-26

### Added

- signed固定小数点formatを表す`SignedFixedPointFormat` protoを追加
- 任意formatの`SignedFixedPointFormatOf::<W, F>`を追加
- Q1.31/Q2.16/Q3.24/Q8.19/Q8.24 presetを追加
- 丸め、飽和、clamp、resize、乗算のraw APIとformat-aware APIを追加
- 丸め境界、符号、幅変換、overflow、format変換、乗算のNative testを追加
