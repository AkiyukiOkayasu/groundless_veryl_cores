# ADAT受信から50MHz差動PDM／I2Sまでの実装計画

## 目的

当面の目標は、ADATで受信したPCM音声を50MHzの差動PDMへ変換すること。
現在このPoCは動作しているが、線形補間したPCM値を2次デルタシグマ変調器へ入力しているため、以下を評価・改善する。

- 補間による周波数特性の劣化
- デルタシグマ変調器の安定性とアイドル音
- ADAT側クロックと50MHz側の長期的な周波数差
- S/MUXを含むチャンネル間のサンプルずれ
- 将来のI2S出力との共通化

## 当面の目標仕様：ADATから高音質50MHz差動PDMへ

DAのアナログ段は十分に改善されているものとし、当面はデジタル経路の品質を主な対象にする。最初の目標は通常ADAT 48kHz、8chの入力を、停止しない50MHz差動PDMへ変換することとする。

```text
AdatRx 48kHz PCM
  → PCM正規化（24bit signed → Q1.31）
  → 4倍帯域制限付きオーバーサンプリング（48kHz → 192kHz）
  → レート追従付き分数遅延補間（Farrowを候補にする）
  → 50MHz連続PCM
  → 2次ΔΣ変調
  → pdm / ~pdm
```

Farrowは分数遅延を評価する補間器であり、アンチイメージング用のローパスフィルタではない。したがって、Farrow単体を高音質化の最終手段にはせず、手前のオーバーサンプリング段にローパス特性を持たせる。48kHz入力の20kHzは約0.417Fsだが、4倍後の192kHzでは約0.104Fsとなるため、Farrowの高域特性劣化を音声帯域から遠ざけられる。

4倍オーバーサンプリングは、まず2段の2倍halfband/polyphase FIRで実装する。`CicInterpolator`は資源量を比較する基準実装として利用できるが、音声帯域のdroopがあるため、最終経路ではCIC単体を採用しない。CICを使う場合は補償FIRを追加する。

初期の品質目標は次を仮基準とする。実装規模と測定結果を見て調整する。

- PCM再構成経路の20Hz〜20kHzの振幅偏差を±0.1dB以内
- 可聴帯域内のレート補正による変調成分を測定可能な限り抑える
- 1kHz正弦波をPDMから理想デジタルLPFで復元したときのTHD+Nを90dB以上
- 0入力、低レベル入力、正負DCでΔΣ変調器が発散・飽和しない
- 50MHzの全クロックでPDMを連続出力し、欠落・停止・チャンネル間の位相不整合を発生させない

### この目標で分離して評価するもの

- ADAT受信とPCMビット整列：完成済み入力として固定し、後段変更の回帰条件にする
- サンプル時刻の揺らぎ：`valid`周期の測定・平滑化・NCO位相増分で評価する
- 再サンプリング：帯域制限付き4倍FIRとFarrowの組み合わせを、PDMとは別に評価する
- ΔΣ変調：50MHzの連続PCMを直接入力し、密度、帯域内ノイズ、アイドル音、安定性を評価する
- 全経路：ADAT相当のPCMとvalid周期からPDMを生成し、理想デジタル復元後の品質を評価する

## 既存プロジェクトから確認できたこと

### ADAT受信は完成済みの入力源として扱う

`FPGA_ADAT`には、次の実機向け経路がすでにある。

```text
ADAT光入力
  → AdatRx
  → 8ch 24bit PCM
  → {pcm, 8'b0} によるQ1.31変換
  → LinearInterpolator × 8
  → DeltaSigma2nd × 8
  → PDM_P / PDM_N
```

ADAT受信は現在のPoCで完璧に動作しており、以降の音質改善では完成済みの入力源として扱う。受信ロジックを作り直したり、ASRC実装の前提として`locked`や`valid`の問題を解決したりする必要はない。

一方、別バージョンの開発時には次のような切り分け記録が残っている。

- RMEを音源にした48kHz、200Hz正弦波で確認している。
- あるバージョンでは`dbg_locked`が約84µs周期でLowになり、フレーム欠落が発生していた。
- そのバージョンではチャンネルごとにノイズ量が異なり、2chの悪化が特に大きかった。
- `LinearInterpolator`をバイパスしてもノイズは変化しなかった。
- 旧バージョンではロックが安定し、全チャンネルに同程度の小さなステップ状ノイズが残った。

これらは過去バージョンの調査記録であり、現在のADAT受信が不完全であることを示すものではない。今後は受信コアを変更する場合の回帰テストや、問題が再発した場合の診断資料として参照する。現在の音質改善では、線形補間、ΔΣ変調、出力レート制御を主な調査対象にする。

### 2次デルタシグマには既存の基準実装がある

`FPGA_Oscillator`の2次デルタシグマは、40bit積分器、入力の`>>> 2`、帰還値`+2^30-1/-2^30`という構成で、50MHz差動PDM出力に使用されている。groundlessの`DeltaSigma2nd`もこの系統を基準にしている。

当面は変調器の式を先に作り変えず、次を基準値として測定する。

- 入力スケーリングとフルスケール余裕
- 0入力のアイドルパターン
- DC密度、正弦波の帯域内ノイズ、THD+N
- 積分器の最大値と長時間安定性

この測定で問題が確認できた場合に限り、帰還係数、入力ゲイン、積分器幅、量子化器を個別に変更する。

### 50MHz差動PDMの実装上の基準

`FPGA_ADAT`と`FPGA_Oscillator`のどちらも、差動出力は同じ1bit値の相補信号として扱う。

```text
pdm_p = pdm
pdm_n = ~pdm
```

`FPGA_Oscillator`では外部ピン直前に出力レジスタを置いている。groundlessではまず組み合わせの相補出力を標準とし、対象FPGAの出力タイミングやピン実装で必要になった場合だけ出力レジスタをラッパー側へ追加する。

### Gowin 50MHz制約

対象の`FPGA_ADAT`はTang Primer 25K（GW5A-25A）で、プロジェクトの要求Fmaxは50.1MHz以上である。別プロジェクトのタイミング資料では、50MHz制約に対してFPGA種類により実測Fmaxが50.141〜51.663MHzの範囲にある。

8chを50MHzで並列に処理するFarrowやpolyphase FIRは、音質だけでなくFmax、LUT、DSP、配線負荷で判断する。各段階で合成可能性を確認し、外部プロジェクトのCPU由来のタイミング結果を音声コア単体の保証値とは解釈しない。

## 前提

- ADAT受信ロジックとPDM変調器は同じ50MHzクロックで動作する。
- コア間のCDCは不要。Async FIFOは使用しない。
- 4倍オーバーサンプラが短時間に生成する4サンプルと、50MHzで連続動作する補間器の計算タイミングを分離するため、同一クロックのVeryl STD FIFOは使用してよい。独自FIFOは作らない。
- ただし、光入力のADAT信号は50MHzに同期していないため、入力端の同期化は必要。これは既存の`Synchronizer`で行う。
- 初期実装は48kHz、8chの通常ADATを対象にする。
- S/MUX2/4は、通常ADATの音質改善が確認できた後に対応する。
- PCM内部形式はsigned Q1.31へ統一する。

## 目標アーキテクチャ

```text
AdatRx
  │  8ch PCM frame + valid + locked + source timing
  ▼
S/MUX／PCM正規化
  │  8chを同じフレームとして扱う
  ▼
共有phase／rate tracker
  │
  ├─ PDM path
  │    ▼
  │  帯域制限付き4倍オーバーサンプラ
  │    │  192kHz PCM窓
  │    ▼
  │  50MHz output tick
  │    ▼
  │  分数遅延補間／PdmAsrc
  │    ▼
  │  DeltaSigma2nd
  │    ▼
  │  pdm / ~pdm
  │
  └─ I2S sample tick
          ▼
      I2sTx
```

PDMの50MHzはPCMのサンプルレートではない。50MHzの各出力周期で、入力PCM列を再構成した瞬時値を生成し、それを1bit変調器へ渡す構成とする。

## 現在の実装

| 領域 | 現在の実装 | 状態 |
| --- | --- | --- |
| ADAT | `AdatRx` | 50MHz受信、8物理スロット、`valid`/`locked`出力 |
| 固定小数点 | `FixedPoint` | Q1.31演算・丸め・飽和 |
| 補間 | `ZeroOrderHold`, `LinearInterpolator`, `CubicLagrangeInterpolator` | 単体Native test済み。3方式のステップ／ランプ／正弦波／インパルス比較CSVベンチマークを追加 |
| ASRC | `LinearAsrc`, `ContinuousLinearAsrc`, `CubicLagrangeAsrc`, `SampleRateTracker` | 汎用stream型と50MHz連続出力型を実装済み。Trackerは周期測定・平滑化まで |
| CIC | `CicDecimator`, `CicInterpolator` | 乗算器なしの間引き・補間。ゲイン補正は後段で行う |
| PDM | `DeltaSigma1st`, `DeltaSigma2nd` | 密度Native test済み。音質評価は未実施 |
| NCO | `NcoTick`, `ClockEnableNco` | 分数比tick生成 |
| FIFO | Veryl STDを直接利用 | 独自FIFOラッパーは削除済み |
| I2S | 未実装 | 将来の出力先 |

主な実装ファイルは[README.md](README.md)のモジュール一覧を参照する。

## 直近の実装スコープ

直近では、固定48kHz入力に対する「直接線形補間」と「4倍HBF＋線形補間」の差を測るところまでを実装する。ADAT受信の変更、入力ジッター追従、Farrow、I2S、S/MUX、PLLはこの実装単位へ含めない。

最初は1chの数値検証を行い、フィルタと補間器の仕様が確定してから8chへ複製する。入力はADAT相当のQ1.31 PCMと`sample_valid`で与え、PDMへ接続する前の50MHz PCMを主な比較対象にする。

### 固定レート比較の構成

直接線形補間と4倍HBF経路は、最終段の連続線形補間器を共用する。

```text
直接線形補間:

48kHz Q1.31 stream
  → Veryl STD FIFO
  → 連続線形補間
  → 50MHz PCM

4倍HBF＋線形補間:

48kHz Q1.31 stream
  → 2倍halfband interpolator
  → 2倍halfband interpolator
  → 192kHz相当の4サンプルburst
  → Veryl STD FIFO
  → 連続線形補間
  → 50MHz PCM
```

HBFの出力`valid`は論理サンプルの順序を表し、物理的に192kHz間隔で発生させる必要はない。各48kHz入力から生成した4サンプルを数クロックのburstとしてFIFOへ格納し、連続線形補間器がNCO位相に従って約260クロックごとに1サンプルずつ消費する。これにより、192kHz用の別tick生成器やHBF内部の実時間スケジューラを作らない。

FIFOはCDCや大容量蓄積には使わず、burstを吸収する同一クロックの小容量バッファに限定する。初期値は深さ8とし、Native testで最大levelとunderflow／overflowを確認する。深さを増やすのは、固定レートtestで不足が確認された場合だけとする。

### 直近に追加するモジュール

`FractionalPhaseAccumulator`、2段用の`HalfbandInterpolator2x`、係数設計スクリプト、
`ContinuousLinearAsrc`、`FourXHalfbandAsrc`、固定レート比較ベンチマークは実装済み。
次はCSV解析結果を基準に、PDM変調器を接続したときの差を分離して測る。

#### `FractionalPhaseAccumulator`

50MHzごとに`phase_increment`を加算し、補間用の小数位相と入力サンプルの進行を出力する。既存の`NcoTick`はclock-enable用として維持し、ASRCの位相生成へ流用しない。

- `phase_increment < 1.0`だけを初期仕様とする
- 1クロックで進む入力サンプル数は0または1
- 直接線形補間では`48_000 / 50_000_000`
- 4倍HBF経路では`192_000 / 50_000_000`
- phase更新、wrap、長時間の平均進行数をNative testで確認する

任意modulus、複数wrap、実クロック出力、PLL相当のループ制御は実装しない。

#### `HalfbandInterpolator2x`

1入力から2個の論理出力サンプルを生成する、固定係数の2倍補間器とする。

- 入出力はQ1.31
- 係数はsigned 18bitを初期候補とする
- halfbandのゼロ係数と対称性を利用する
- 50MHzと48kHzの余裕を利用し、1つの積和器を時分割する
- `valid`/`ready`で2サンプルのburstを受け渡す
- 係数の任意runtime変更や汎用FIR化は行わない

2段で同じRTLを使い、係数セットだけを変えられる構成を目標にする。ただし、Verylのparameter配列によって実装が複雑になる場合は、係数ROMを段ごとに分ける。汎用化のために新しい言語機能へ依存しない。

係数はRTL内で試行錯誤せず、外部の設計スクリプトで量子化後の応答を確認してから固定値として追加する。最初の目標値は次とする。

- 2段合成で20Hz〜20kHzの振幅偏差を±0.05dB以内
- 48kHz入力の最初のイメージ帯域を80dB以上抑圧
- Q1.31フルスケール近傍で内部accumulatorがoverflowしない

tap数は先に固定せず、上記を満たす最小の奇数tap数を選ぶ。資源削減は、係数応答が確定した後に行う。

#### `ContinuousLinearAsrc`

入力FIFOから3サンプルの窓を先読みし、50MHzの全クロックで線形補間値を出力する。

- 位相は`FractionalPhaseAccumulator`から受け取る
- 通常動作中は出力を停止しない
- phase wrap時には先読み済みサンプルへ窓を進める
- 起動時に必要なサンプルが揃うまでは0を出力する
- 通常動作中のunderflow／overflowはsticky errorとして検出する
- `output_valid`による50MHz出力停止は行わない

既存の`LinearAsrc`は汎用stream ASRCとして残す。`ContinuousLinearAsrc`から共通化できる処理が明確になった場合だけ、後から内部部品を抽出する。

`ContinuousLinearAsrc`には起動時の`STARTUP_LEVEL`を設ける。直接入力では小さな値を使い、
4倍HBFのburst経路では深さ8 FIFOのうち6サンプルを蓄積してから位相を開始する。
これにより、HBFの初回burstと50MHz出力の消費開始が重なって起動直後にFIFOが空になることを避ける。

#### 固定レート比較ベンチマーク

`src/integration/fixed_rate_asrc_benchmark.veryl`は、実際の48kHz／50MHz比で同じ正弦波を
直接線形補間経路と4倍HBF＋線形補間経路へ入力する。1kHz、10kHz、18kHz、20kHzを各200,000
クロック生成し、50MHz PCMをCSVへ出力する。起動過渡は解析側で除外する。

```text
veryl test --ignored -t fixed_rate_asrc_benchmark
python3 tools/analyze_fixed_rate_asrc.py target/fixed_rate_asrc_benchmark.csv
```

解析スクリプトは外部パッケージを使わず、既知周波数への最小二乗フィットから振幅、dBFS、
4倍HBFと直接経路のゲイン差、残差RMSを求める。underflowはケース全体でsticky値を検査する。
これはADATのvalid周期やジッタを含まない、固定レート時のPCM経路比較である。

初回結果（`--discard-cycles 100000`、underflowは全ケース0）は次の通りである。

| tone | direct | 4x HBF | 4x - direct |
| ---: | ---: | ---: | ---: |
| 1kHz | −0.017dBFS | −0.005dBFS | +0.012dB |
| 10kHz | −1.263dBFS | −0.081dBFS | +1.181dB |
| 18kHz | −4.226dBFS | −0.255dBFS | +3.970dB |
| 20kHz | −5.284dBFS | −0.315dBFS | +4.969dB |

これは補間前の48kHzサンプルを直接線形補間する場合、20kHz付近で生じるsinc由来の
振幅低下が支配的になり得ることを示す。4倍HBFの結果は改善しているが、HBFの阻止帯域、
量子化、PDM変調器を含まないため、最終的な音質差とは解釈しない。

### 8ch化の方針

位相アキュムレータは8chで1個を共有する。HBFの履歴、FIFO、線形補間窓、ΔΣ変調器はチャンネルごとに持つ。

最初から8ch統合moduleは作らず、1chの固定小数点結果とFIFO占有量が確定した後に単純複製する。チャンネル間の`valid`と位相が一致することだけを統合testで確認する。

### 直近スコープの完了条件

- 縮小したクロック比を使うNative testで、phase wrap、FIFO補充、連続出力を短時間に検証できる
- 実際の48kHz／50MHz比を使うignored benchmarkで、起動後に50MHz PCMの欠落がない（達成）
- 深さ8のFIFOで固定レート時にunderflow／overflowが発生しない（underflow確認済み）
- HBFのインパルス応答が、係数量子化を含む外部固定小数点モデルと一致する
- 直接線形補間と4倍HBF＋線形補間について、少なくとも1kHz、10kHz、18kHz、20kHzの振幅誤差を同じ解析スクリプトで比較できる（達成）
- PCM比較結果を確認してからだけ、`DeltaSigma2nd`を含むPDM評価へ進む

Native testでは長時間のFFTを行わず、制御と既知値だけを確認する。実クロック比、CSV出力、周波数解析は個別のignored benchmarkへ分離する。

### この段階で作らないもの

- 独自Sync FIFO、Async FIFO
- FIFO levelを使ったレートサーボ
- SampleRateTrackerの外れ値除去やホールドオーバー
- Farrowとの統合
- PLLまたは実クロック生成
- 任意レート、任意tap数、runtime係数変更に対応する汎用フィルタ
- ADATからPDMまでを一度に検証する巨大testbench

## 実装フェーズ

### Phase 0: ADAT入力の回帰基準を固定

ADAT受信は完成済みとして、現在の動作を回帰基準に固定する。受信ロジックの改善をこの計画の前提条件にはしない。

- `locked`が連続して維持されること
- `valid`が期待サンプルレートで1回だけ発生すること
- `frame_clk`とチャンネル完了位置が一致すること
- `locked`解除時に後段へ古いPCMを流さないこと

このフェーズの目的は受信品質の再調査ではなく、後段を変更したときに入力条件が変わっていないことを確認することである。グリッチ／ジッタ試験は、将来`AdatRx`を変更する場合だけ実施する。

参照する既存計画:

- `FPGA_ADAT/.opencode/plans/adat_noise_investigation.md`
- `FPGA_ADAT/tests/glitch_jitter_plan.md`

### Phase 1: 音質評価基盤

RTLを大きく変更する前に、固定入力に対するPDMの品質を測定できるようにする。

評価信号:

- 無入力
- DC（正・負・0）
- 1kHz正弦波
- 周波数スイープ
- マルチトーン
- インパルス

評価項目:

- PDM密度とDC誤差
- 低域の振幅・位相特性
- SNR、THD+N、帯域内ノイズ
- アイドルトーンと周期パターン
- 変調器内部状態の発散・飽和

`veryl test`は機能回帰に使用する。FFT、SNR、THD+Nなどの音質指標は、固定PDM列を外部の数値解析モデルへ渡して評価する。Veryl Native testだけで音質を判定しない。

補間器単体の比較では、入力サンプル列と位相列を固定し、`ZeroOrderHold`、`LinearInterpolator`、4点窓の`CubicLagrangeInterpolator`へ同じ値を与える。ADATの`valid`間隔、FIFO、ΔΣ変調器はこの測定へ混ぜない。定量評価は実装ファイルから分離した`packages/interpolation/src/interpolator_benchmark.veryl`で行い、`$tb::file`で`target/interpolator_benchmark.csv`を書き出す。

CSVは2の補数の固定小数点値を出力する。`case=0..3`はステップ・ランプ・振幅反転、`case=4`は64サンプル長のインパルス列、`case=5..8`は0.05／0.15／0.25／0.40 Fsの正弦波である。正弦波は各64入力サンプル区間を256位相へ展開する。`sample_index`、`phase`、`frequency_milli_fs`を使って入力サンプルレートと出力点を復元し、外部数値解析で最大誤差・平均誤差・インパルス応答・周波数応答を求める。

このベンチマークにはADATの`valid`間隔、FIFO、ΔΣ変調器を接続しない。したがって、ここで測るのは補間カーネルそのものの差であり、クロックジッターやレート追従の影響は含まれない。

解析は依存パッケージなしの[`packages/interpolation/tools/analyze_interpolator_benchmark.py`](packages/interpolation/tools/analyze_interpolator_benchmark.py)で行う。CSVの列、2の補数、3方式間の差、phase列の連続性を検証したうえで、最大差・平均差・RMS差、正弦波の理想連続正弦波に対する誤差、インパルス応答のDCゲイン、指定周波数の相対dBを出力する。

```text
cd packages/interpolation
veryl test --ignored -t interpolator_benchmark
python3 tools/analyze_interpolator_benchmark.py target/interpolator_benchmark.csv
python3 tools/analyze_interpolator_benchmark.py --format json target/interpolator_benchmark.csv
```

FFTをVeryl Native testへ実装したり、まだ安定していないRust componentへ依存したりせず、RTL出力の生成はVeryl、数値解析は標準Pythonへ分離する。

### Phase 2: PCM入力インターフェースの整理

`AdatRx`の出力を、後段が扱いやすいフレームストリームへ整理する。

- 24bit ADAT PCMをsigned Q1.31へ変換
- `valid`時に8chを同時に受理
- `locked`未成立時はミュートまたは無効化
- 8chを共通フレームとして扱い、チャンネル間ずれを防止
- `frame_time`または入力サンプル周期を外部へ公開
- S/MUX2/4は論理チャンネル再構成を分離モジュールにする。`FPGA_ADAT`の`AdatFrameBuffer`で行っている「物理ch1-4、ch5-8を時間方向に並べ替える」処理を仕様化し、groundlessの`Smux2Packer`/`Smux2Unpacker`と同じサンプル順に固定する

ADATの`frame_time`は現在`TimingTracker`内部にある。まず実測周期を出力できるようにし、入力レート追従の基礎にする。

### Phase 3: 2次デルタシグマ変調器の検証・修正

現在の`DeltaSigma2nd`を、1次変調器と比較しながら検証する。

- Q1.31入力のスケーリングを確認
- 入力振幅の上限にヘッドルームを設ける
- 積分器のガードビットと飽和方針を決める
- 0入力時のアイドル音を確認
- 正負フルスケール近傍の安定性を確認
- 長時間シミュレーションで発散しないことを確認

2次化が常に音質改善になるとは限らない。まず安定性と帯域内ノイズを確認し、必要なら帰還係数・入力スケーリング・量子化器を見直す。

差動PDMは変調器を2個使わず、次のように生成する。

```text
pdm_p = pdm
pdm_n = ~pdm
```

### Phase 3.5: CICレート変換の基礎コア

`CicDecimator`と`CicInterpolator`は、乗算器を使わずに粗いレート変換を行う部品として維持する。現在は次の仕様に限定している。

- 間引き側は入力`valid`を`DECIMATION`個受けるごとに1出力を生成する
- 補間側は入力を櫛形フィルタへ通し、ゼロ挿入後に`INTERPOLATION`倍の出力を連続生成する
- `ACCUMULATOR_WIDTH`内でのラップアラウンドを許容するため、十分なガードビットを利用者が確保する
- 通過帯域droop、遅延、定常ゲインの補正はこのコアの責務にせず、後段の固定小数点スケーラ／FIRで補正する

CICは音声帯域の最終フィルタにはせず、まずNative testでDCゲイン、インパルス応答、オーバーフロー余裕を確認する。必要なら後段FIRを追加する。

### Phase 4: 50MHz PDM専用ASRC

現在の`LinearAsrc`/`CubicLagrangeAsrc`は`output_ready`による停止を許容する汎用stream型である。PDMは50MHzごとに連続してbitを出す必要があるため、まず`FractionalPhaseAccumulator`と`ContinuousLinearAsrc`を作る。PDM向けのwrapperは、これらと`DeltaSigma2nd`を接続するだけにする。

要求仕様:

- 起動完了後は毎50MHzクロックでPCMを更新
- 初期サンプル不足時だけミュート
- 通常動作中は出力を停止しない
- 4倍オーバーサンプラのburstは同一クロックのVeryl STD FIFOで受ける
- FIFOは深さ8から開始し、アンダーフロー／オーバーフローを検出する
- 全チャンネルで共有phaseを使う
- まず直接線形補間を基準にし、次に4倍HBF＋線形補間へ切り替えて比較する
- Farrowは4倍HBF＋線形補間の測定結果で必要性が確認された場合だけ接続する

位相増分は次式で表す。

```text
phase_increment = Fs_input / 50_000_000 × 2^PHASE_WIDTH
```

192kHz入力、Q0.32の場合は丸めて16,492,674となる。PDM経路では通常0〜1未満の入力サンプル進行量になるため、現在の`ratio`という名前より`phase_increment`の方が意味が明確である。入力ADATのレート変動は、4倍オーバーサンプラの入力レートとこの最終段の位相増分の両方へ一貫して反映する。

### Phase 5: 補間品質の向上

次の順で音質と回路規模を比較する。

1. 線形補間（現状の基準）
2. 4倍halfband/polyphase FIR + 線形補間
3. 4倍halfband/polyphase FIR + 4点Farrow補間
4. 必要なら8倍オーバーサンプリングまたは8〜32タップpolyphase FIR

Farrowについては、`packages/interpolation/src/cubic_lagrange_interpolator.veryl`と`packages/asrc/src/cubic_lagrange_asrc.veryl`に4点窓の補間器とASRC、実装内の既知値Native testをまとめ、正弦波・インパルス応答の比較ベンチマークまで実装済みである。今後はFarrow単体の改善よりも、手前の帯域制限付きオーバーサンプリングとの組み合わせを主な評価対象にする。

- 2倍halfband/polyphase FIRを2段接続した4倍オーバーサンプラ
- FIR係数の量子化誤差、遅延、通過帯域droop、阻止帯域減衰
- 係数量子化後の丸め
- 出力飽和
- 負値を含むテスト
- インパルス応答test
- 周波数応答の外部評価

8chを50MHzで並列処理するため、FarrowやFIRへ進む前にDSP使用量とFmaxを確認する。音質差が小さい場合は線形補間を維持し、回路規模を優先する。

### Phase 6: 入力レート追従

固定48kHz比だけでは、ADAT側とFPGAの50MHz側の周波数差によりFIFOレベルが長期的に変化する。

次のデジタル追従を追加する。

- `valid`間隔を測定し、整数ではなく固定小数点の周期推定値を作る
- 推定周期のLPFだけでなく、外れ値検出、ロック成立、valid欠落時のホールドオーバーを設ける
- 推定周期からphase incrementまたは周波数偏差を算出する
- FIFOレベルを目標値へ戻す低帯域補正
- phase incrementを急変させない
- 音声帯域へレート補正ノイズを入れない
- 入力レート変化時もアンダーフローしない

`SampleRateTracker`は周期測定と平滑化だけを担当し、phase accumulatorやFIFO制御はASRC側へ分離する。48kHz入力では50MHzクロック上の1041/1042周期列が正常な量子化結果なので、単純な整数LPFの出力をそのまま使わない。ここではPLLを使わず、NCO／phase accumulatorとFIFOレベル制御を使う。PDMの出力クロック自体は既存の50MHzを維持する。

初期版の`SampleRateTracker`は「`sample_valid`の立ち上がり相当の到着時刻を数える → 2回目以降に生周期を出す → 固定小数点の一次IIRで平滑化する → 指定回数の測定後に`locked`を立てる」という責務だけを持つ。したがって、質問の「valid間隔を測ってローパスをかけるだけか」に対しては、初期版についてはほぼその通りだが、製品用のレート追従としては不十分である。

次の版で、外れ値除外、valid欠落のタイムアウト／ホールドオーバー、許容範囲外レートの拒否、レート変化時の再ロックを追加する。平滑化周期をそのまま出力tickへ変換せず、`phase_increment`の基準値とFIFOレベル補正を別のサーボとして持たせる。

### Phase 7: S/MUX対応

通常ADATの48kHz・8ch経路が安定した後に対応する。

- S/MUX2の96kHz・4ch再構成
- S/MUX4の192kHz・2ch再構成
- 44.1kHz系の対応
- User bitだけではS/MUX2とS/MUX4を完全には区別できないため、仕様と設定方法を決める
- 論理チャンネルのサンプル順をNative testで固定する

### Phase 8: I2S出力

ASRCをPDM専用にせず、出力tickを差し替えられる共通コアとして利用する。

```text
PDM:  output_tick = 50MHz
I2S:  output_tick = 48kHzまたは96kHz
```

I2Sでは次を実装する。

- 24/32bit stereo data
- I2S standardのLRCLK遅延
- sample valid/readyとの接続
- 50MHzからの分数比bit tick生成
- master/slaveの役割を明確化

50MHzからNCOでI2S clockを作ることはできるが、外部codecが低ジッタのMCLK/BCLKを要求する場合は、最終的にPLLまたは外部クロックを検討する。サンプルレート変換そのものはNCOで行う。

## 検証方針

RTL変更時:

```text
veryl fmt
veryl check
veryl test
```

必要に応じて生成確認として`veryl build`も実行する。

Native testで確認する項目:

- 固定小数点の符号・丸め・飽和
- NCOの平均tick周期
- FIFOの入力受理とアンダーフロー検出
- ASRCの位相連続性
- 線形／Cubic Lagrange補間の既知値
- デルタシグマの密度と長時間安定性
- ADATからPDMまでの固定レートloopback
- I2Sのbit順、LRCLK、valid/ready

外部数値解析で確認する項目:

- SNR
- THD+N
- 周波数応答
- 帯域内ノイズ
- アイドルトーン
- 入力レート変動時のサイドバンド

実機検証では、最初に1chまたは2chでPDM波形とアナログ再生後の音を確認し、その後8chへ拡張する。

## 当面の実装順

1. HBF係数の設計スクリプトと量子化後の周波数応答を作り、2段分の係数とtap数を固定
2. `FractionalPhaseAccumulator`と同一ファイルのNative testを実装
3. `HalfbandInterpolator2x`と同一ファイルのインパルス／DC／負値／burst順序testを実装
4. `HalfbandInterpolator2x`を2段接続し、1入力から4出力になることを検証
5. `ContinuousLinearAsrc`を深さ8のVeryl STD FIFOと3サンプル窓で実装
6. 直接線形補間と4倍HBF＋線形補間を同じ50MHz PCMベンチマークで比較
7. 既存`DeltaSigma2nd`へ両経路を接続し、PDM復元後のSNR、THD+N、帯域内ノイズを比較
8. ここまでの結果からHBFのtap数とFarrow追加の必要性を判断
9. 固定レート経路の確定後に、`SampleRateTracker`、phase increment更新、FIFO level servoを追加
10. 1chで確定した構成を8chへ複製し、ADAT入力へ統合
11. S/MUX2/4とI2S送信器は通常ADATのPDM経路完成後に実装

## 既存プロジェクトの参照先

実装や判断の根拠として、次のファイルを参照する。

| 参照 | 確認できる内容 |
| --- | --- |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_ADAT/README.md` | 実機構成、ビルド手順、ADAT→PDMの目的 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_ADAT/Firmware/Gowin/RTL/Veryl_ADATDecoder/src/top.veryl` | 8chフレームバッファ、Q1.31変換、線形補間、差動PDMの統合例 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_ADAT/Firmware/Gowin/RTL/Veryl_ADATDecoder/src/linearInterpolator.veryl` | 現在の入力周期測定型線形補間の実装とNative test |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_ADAT/.opencode/plans/adat_noise_investigation.md` | 実機ノイズとロック不安定の切り分け結果 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_ADAT/tests/glitch_jitter_plan.md` | ADATグリッチ／ジッタ耐性テスト計画 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_Oscillator/Firmware/Gowin/fpgaOscillator/src/deltaSigma.sv` | 40bit積分器、入力スケーリング、帰還値の基準実装 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_Oscillator/Firmware/Gowin/fpgaOscillator/src/top.sv` | 4ch差動PDMと出力レジスタの統合例 |
| `/Users/akiyuki/Documents/AkiyukiProjects/EurorackProjects/FPGA_Oscillator/docs/timing-analysis.md` | 50MHz制約とGowin合成後Fmaxの記録 |

## 現時点で採用しないもの

- 内部CDC用Async FIFO
- PDM用PLL
- いきなり大規模polyphase FIRへ置き換えること
- 音質指標なしで補間器や変調器の次数だけを増やすこと
