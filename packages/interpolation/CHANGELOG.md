# Changelog

## [Unreleased]

### Added

- ZOH、linear、cubic Lagrange補間kernelを独立packageへ移動
- `FarrowInterpolator`を`CubicLagrangeInterpolator`へ改名
- signed sample、Q0.phase、nearest ties to even、saturationを明示する数値APIと全rounding mode／小幅全探索testを追加
- Verylのcross-package generic制約を回避する一時adapterと、将来の削除条件を文書化
