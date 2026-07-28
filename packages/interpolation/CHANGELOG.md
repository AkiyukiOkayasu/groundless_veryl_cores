# Changelog

## [Unreleased]

- 各testのdoc commentを検証目的が分かる表現へ統一
### Added

- linear、cubic Lagrange補間kernelを独立packageへ移動
- `FarrowInterpolator`を`CubicLagrangeInterpolator`へ改名
- signed sample、Q0.phase、nearest ties to even、saturationを明示する数値APIと全rounding mode／小幅全探索testを追加
- fixedpoint project-scopeの`resize`をlinear／cubicから直接呼び出す構成へ変更

### Changed

- `ZeroOrderHold`を公開APIから外し、比較ベンチマーク専用の`BenchmarkZeroOrderHold`へ整理
