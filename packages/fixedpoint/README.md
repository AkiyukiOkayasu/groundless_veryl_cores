# gndless_fixedpoint

Veryl向けのsigned固定小数点演算ライブラリです。

formatを表すproto package、任意format、名前付きQ形式preset、丸め、飽和、
clamp、resize、乗算を提供します。任意幅を受け取るraw generic演算は
project-scope functionとして公開します。固定小数点値は合成可能な
`signed logic<WIDTH>`として扱い、format間の変換はformat-aware APIで明示します。

project-scope raw APIは`raw_round_shift`、`raw_saturate`、`raw_clamp`、`resize`、
`raw_multiply`、`raw_multiply_resize`です。parameterized moduleからは
`fixedpoint::resize::<...>`のようにmodule parameterを直接渡せます。
format packageを受け取る型付き演算は`SignedFixedPoint`にまとめています。

## 利用例

```toml
[dependencies]
fixedpoint = {
    project = "gndless_fixedpoint",
    github = "AkiyukiOkayasu/gndless-fixedpoint-veryl",
    version = "0.1.0"
}
```

```veryl
import fixedpoint::*;

let input : Q1_31::Raw;
let output: Q8_24::Raw;

assign output = SignedFixedPoint::convert::<
    Q1_31,
    Q8_24,
    FixedPoint::RoundingMode::NEAREST_TIES_TO_EVEN,
    FixedPoint::OverflowMode::SATURATE,
>(input);
```

## 開発

現在は`groundless_veryl_cores`リポジトリ内のinner projectとして開発しています。
APIとリリース手順が安定した後、
`AkiyukiOkayasu/gndless-fixedpoint-veryl`へ分離する予定です。
