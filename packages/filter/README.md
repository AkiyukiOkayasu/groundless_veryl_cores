# gndless_filter

CIC、2倍halfband、shift型LPF/HPFを所有します。CIC/halfband/shift filterを個別packageへ分割せず、audio rate変換用filter群として管理します。

公開APIは`CicDecimator`、`CicInterpolator`、`HalfbandInterpolator2x`、`LpfShift*`、`HpfShift*`です。依存はVeryl stdのみです。

現行APIはraw signed/unsignedの入出力を使い、format generic化は行っていません。CICの内部accumulator幅、decimation/interpolation比、halfbandの係数・burst/enable契約、shift量と出力切り詰めは各module doc commentを正とします。clock/resetは同期、streamは`enable`で進み、stall中は状態を保持します。

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。係数設計ツールは`tools/design_halfband_coefficients.py`です。
