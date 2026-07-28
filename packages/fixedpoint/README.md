# gndless_fixedpoint

Veryl向けのsigned固定小数点演算ライブラリです。

formatを表すproto package、任意format、名前付きQ形式preset、丸め、飽和、
resize、変換、全幅乗算を提供します。演算はすべてproject-scope functionとして
公開します。固定小数点値は合成可能な
`signed logic<WIDTH>`として扱い、format間の変換はformat-aware APIで明示します。

公開APIは`round_shift`、`saturate`、`resize`、`convert`、
`multiply`、`multiply_resize`です。parameterized moduleからは
`fixedpoint::resize::<...>`のようにmodule parameterを直接渡せます。format間の変換には
`fixedpoint::convert::<Q1_31, Q8_24, ...>`のようにformat packageを指定します。

`round_shift`と`saturate`は、用途に不要なgeneric引数を指定させない
`resize`の安全な専用APIです。`multiply`はVerylの式幅に依存せず
`A_WIDTH + B_WIDTH`の全幅積を返し、`multiply_resize`は全幅積から出力formatへの
変換までを一括して行います。

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

assign output = convert::<
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
