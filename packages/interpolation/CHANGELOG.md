# Changelog

## [Unreleased]

### Added

- ZOH、linear、cubic Lagrange補間kernelを独立packageへ移動
- `FarrowInterpolator`を`CubicLagrangeInterpolator`へ改名
- signed sample、Q0.phase、nearest ties to even、saturationを明示する数値APIと全rounding mode／小幅全探索testを追加
- Verylのcross-package generic引数制約に対応するproject-scope resize helperを追加し、
  仕様変更後の削除条件を文書化
