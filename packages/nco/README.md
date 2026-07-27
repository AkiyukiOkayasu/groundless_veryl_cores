# gndless_nco

unsigned modular phaseを生成するNCO primitiveです。波形変換は所有せず、オシレーターやASRCの位相源に使います。

公開APIは`NcoTick`、`ClockEnableNco`、`FractionalPhaseAccumulator`、`Phase`、`Phasor`です。依存はVeryl stdのみです。

`Phase`は32bitのunsigned phase、`step_t`は符号付き48bit phase stepです。accumulatorは2の補数moduloでwrapし、`enable`停止中は状態を保持します。reset/restart/updateの優先順位、tick/advanceは各moduleの日本語doc commentに記載しています。`Phasor`は同期reset、`phase_rst`、1-cycleの`eoc`を持ち、latencyは0（`phase`出力はregister更新後）です。

```veryl
inst nco: nco::FractionalPhaseAccumulator #( WIDTH: 32 ) (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
