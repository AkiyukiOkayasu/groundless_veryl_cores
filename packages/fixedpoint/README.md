# gndless_fixedpoint

Veryl向けのsigned固定小数点演算ライブラリです。

formatを表すproto package、任意format、名前付きQ形式preset、丸め、飽和、
clamp、resize、乗算を提供します。固定小数点値は合成可能な
`signed logic<WIDTH>`として扱い、format間の変換はformat-aware APIで明示します。

任意幅のraw値を変換するgeneric関数はproject-scopeの`resize::<...>`です。
VerylのSystemVerilog出力制約により、module parameterをgeneric引数へ渡せる形を
維持するため、`SignedFixedPointRaw` packageの外に定義しています。

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
