# ADAT受信から50MHz差動PDM／I2Sまでの実装計画

## 目的

当面の目標は、ADATで受信したPCM音声を50MHzの差動PDMへ変換すること。
現在このPoCは動作しているが、線形補間したPCM値を2次デルタシグマ変調器へ入力しているため、以下を評価・改善する。

- 補間による周波数特性の劣化
- デルタシグマ変調器の安定性とアイドル音
- ADAT側クロックと50MHz側の長期的な周波数差
- S/MUXを含むチャンネル間のサンプルずれ
- 将来のI2S出力との共通化

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
| 補間 | `LinearInterpolator`, `FarrowInterpolator` | 単体Native test済み |
| ASRC | `LinearAsrc`, `FarrowAsrc` | 汎用stream型。PDM連続出力用には未分離 |
| PDM | `DeltaSigma1st`, `DeltaSigma2nd` | 密度Native test済み。音質評価は未実施 |
| NCO | `NcoTick`, `ClockEnableNco` | 分数比tick生成 |
| FIFO | Veryl STDを直接利用 | 独自FIFOラッパーは削除済み |
| I2S | 未実装 | 将来の出力先 |

主な実装ファイルは[README.md](README.md)のモジュール一覧を参照する。

## 実装フェーズ

### Phase 0: 音質評価基盤

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

### Phase 1: PCM入力インターフェースの整理

`AdatRx`の出力を、後段が扱いやすいフレームストリームへ整理する。

- 24bit ADAT PCMをsigned Q1.31へ変換
- `valid`時に8chを同時に受理
- `locked`未成立時はミュートまたは無効化
- 8chを共通フレームとして扱い、チャンネル間ずれを防止
- `frame_time`または入力サンプル周期を外部へ公開
- S/MUX2/4は論理チャンネル再構成を分離モジュールにする

ADATの`frame_time`は現在`TimingTracker`内部にある。まず実測周期を出力できるようにし、入力レート追従の基礎にする。

### Phase 2: 2次デルタシグマ変調器の検証・修正

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

### Phase 3: 50MHz PDM専用ASRC

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

### Phase 4: 補間品質の向上

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

### Phase 5: 入力レート追従

固定48kHz比だけでは、ADAT側とFPGAの50MHz側の周波数差によりFIFOレベルが長期的に変化する。

次のデジタル追従を追加する。

- `frame_time`から初期phase incrementを設定
- FIFOレベルを目標値へ戻す低帯域補正
- phase incrementを急変させない
- 音声帯域へレート補正ノイズを入れない
- 入力レート変化時もアンダーフローしない

ここではPLLを使わず、NCO／phase accumulatorとFIFOレベル制御を使う。PDMの出力クロック自体は既存の50MHzを維持する。

### Phase 6: S/MUX対応

通常ADATの48kHz・8ch経路が安定した後に対応する。

- S/MUX2の96kHz・4ch再構成
- S/MUX4の192kHz・2ch再構成
- 44.1kHz系の対応
- User bitだけではS/MUX2とS/MUX4を完全には区別できないため、仕様と設定方法を決める
- 論理チャンネルのサンプル順をNative testで固定する

### Phase 7: I2S出力

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

1. PCM24→Q1.31変換と8chフレーム境界の整理
2. `DeltaSigma2nd`の長時間・音質評価
3. 固定48kHz→50MHzの`PdmAsrc`を線形補間で実装
4. Farrow補間へ切り替えて比較
5. `frame_time`公開と入力レート追従
6. S/MUX2/4対応
7. I2S送信器を同じASRC出力へ接続

## 現時点で採用しないもの

- 内部CDC用Async FIFO
- PDM用PLL
- いきなり大規模polyphase FIRへ置き換えること
- 音質指標なしで補間器や変調器の次数だけを増やすこと

