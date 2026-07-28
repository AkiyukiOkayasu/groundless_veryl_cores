# Changelog

このプロジェクトの注目すべき変更を記録します。

## [Unreleased]

- 各testのdoc commentを検証目的が分かる表現へ統一

### Changed

- 公開policy packageをproject名と重複する`FixedPoint`から`Types`へ改名
- monorepo内の`packages/fixedpoint/` inner projectとして他packageから直接参照する構成を確定
- raw generic演算をproject-scope functionへ統一し、parameterized moduleから直接利用可能に変更
- `multiply_resize`をproject-scopeの`multiply`と`resize`を組み合わせる実装へ整理
- `SignedFixedPoint` packageを廃止し、`convert`を含む演算をflatなproject-scope APIへ統一
- 固定小数点固有でない`clamp`を削除し、`round_shift`と`saturate`を`resize`利用の専用APIへ整理
- 単独リポジトリでの検証手順をREADMEへ追加

## [0.1.0] - 2026-07-26

### Added

- signed固定小数点formatを表す`SignedFixedPointFormat` protoを追加
- 任意formatの`SignedFixedPointFormatOf::<W, F>`を追加
- Q1.31/Q2.16/Q3.24/Q8.19/Q8.24 presetを追加
- 丸め、飽和、clamp、resize、乗算のraw APIとformat-aware APIを追加
- 丸め境界、符号、幅変換、overflow、format変換、乗算のNative testを追加
