# gndless_oscillator

NCOのphaseからsine、triangle、saw、square、white/pink noiseを生成します。公開APIは`SineWaveCore`、`SineWaveLerpCore`、`SineOscillator`、`SineOscillatorLerp`、`TriangleWaveCore`、`TriangleOscillator`、`SawWaveCore`、`SawOscillator`、`SquareWaveCore`、`PwmSquareOscillator`、`MultiWaveCore`、`MultiWaveOscillator`、`WhiteNoise`、`PinkNoise`、`WaveTypes`です。ROM moduleは内部APIです。

依存は`fixedpoint`と`nco`です。phase/phase stepは`nco::Phase`、波形出力は現行どおりQ8.24 raw signed値です。ROM coreは1 clock latency、純粋なwave coreは入力phaseに対して組み合わせ、oscillator wrapperは`nco::Phasor`の同期resetと`phase_rst`を使います。振幅、duty、noise seed/stateの契約は各module doc commentを正とします。

```veryl
inst osc: oscillator::SineOscillator (...);
```

ROM生成ツールとchecked-in dataは`tools/sinetable/`にあります。検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
