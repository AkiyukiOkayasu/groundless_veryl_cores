# ADAT受信から50MHz差動PDM／I2Sまでの実装計画

## 目的

当面の目標は、ADATで受信したPCM音声を50MHzの差動PDMへ変換すること。
現在このPoCは動作しているが、線形補間したPCM値を2次デルタシグマ変調器へ入力しているため、以下を評価・改善する。

- 補間による周波数特性の劣化
- デルタシグマ変調器の安定性とアイドル音
- ADAT側クロックと50MHz側の長期的な周波数差
- S/MUXを含むチャンネル間のサンプルずれ
- 将来のI2S出力との共通化

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
- コア間のCDCは不要。Async FIFOも使用しない。
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
  ├─ 50MHz output tick
  │       ▼
  │   PdmAsrc
  │       ▼
  │   DeltaSigma2nd
  │       ▼
  │   pdm / ~pdm
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
| 補間 | `ZeroOrderHold`, `LinearInterpolator`, `FarrowInterpolator` | 単体Native test済み。ステップ／ランプ／インパルス比較CSVベンチマークを追加 |
| ASRC | `LinearAsrc`, `FarrowAsrc`, `SampleRateTracker` | 汎用stream型。PDM連続出力用には未分離。Trackerは周期測定・平滑化まで |
| CIC | `CicDecimator`, `CicInterpolator` | 乗算器なしの間引き・補間。ゲイン補正は後段で行う |
| PDM | `DeltaSigma1st`, `DeltaSigma2nd` | 密度Native test済み。音質評価は未実施 |
| NCO | `NcoTick`, `ClockEnableNco` | 分数比tick生成 |
| FIFO | Veryl STDを直接利用 | 独自FIFOラッパーは削除済み |
| I2S | 未実装 | 将来の出力先 |

主な実装ファイルは[README.md](README.md)のモジュール一覧を参照する。

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

補間器単体の比較では、入力サンプル列と位相列を固定し、`ZeroOrderHold`と`LinearInterpolator`へ同じ値を与える。ADATの`valid`間隔、FIFO、ΔΣ変調器はこの測定へ混ぜない。`interpolator_benchmark`は`$tb::file`で`target/interpolator_benchmark.csv`を書き出す。

```text
veryl test --ignored -t interpolator_benchmark
```

CSVは2の補数の固定小数点値を出力する。`case=0..3`はステップ・ランプ・振幅反転、`case=4`は64サンプル長のインパルス列である。`sample_index`と`phase`を使って入力サンプルレートと出力点を復元し、外部数値解析で最大誤差・平均誤差・インパルス応答・周波数応答を求める。

このベンチマークにはADATの`valid`間隔、FIFO、ΔΣ変調器を接続しない。したがって、ここで測るのは補間カーネルそのものの差であり、クロックジッターやレート追従の影響は含まれない。

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

現在の`LinearAsrc`/`FarrowAsrc`は`output_ready`による停止を許容する汎用stream型である。PDMは50MHzごとに連続してbitを出す必要があるため、専用の`PdmAsrc`を作る。

要求仕様:

- `output_tick`は毎50MHzクロックで発生
- 初期サンプル不足時だけミュート
- 通常動作中は出力を停止しない
- 入力は同期FIFOへフレーム単位で格納
- FIFOアンダーフロー／オーバーフローを検出
- 全チャンネルで共有phaseを使う
- 補間器は最初に線形、次にFarrowへ切り替えて比較する

位相増分は次式で表す。

```text
phase_increment = Fs_input / 50_000_000 × 2^PHASE_WIDTH
```

48kHz入力、Q0.32の場合は約4,123,169となる。PDM経路では通常0〜1未満の入力サンプル進行量になるため、現在の`ratio`という名前より`phase_increment`の方が意味が明確である。

### Phase 5: 補間品質の向上

次の順で音質と回路規模を比較する。

1. 線形補間（現状の基準）
2. 4点Farrow補間
3. 必要なら8〜32タップpolyphase FIR

Farrowでは以下を追加する。

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
- 線形／Farrow補間の既知値
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

1. ADATの現行`locked/valid`を回帰基準として固定
2. PCM24→Q1.31変換と8chフレーム境界の整理
3. `DeltaSigma2nd`を現行式のまま長時間・音質評価
4. 固定48kHz→50MHzの`PdmAsrc`を線形補間で実装
5. Farrow補間へ切り替えて線形補間との差を測定
6. `frame_time`公開と入力レート追従
7. S/MUX2/4対応
8. I2S送信器を同じASRC出力へ接続

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
