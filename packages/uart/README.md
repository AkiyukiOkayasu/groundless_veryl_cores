# gndless_uart

非同期入力からbyteを受信する`UartRx`を提供します。MIDI message parserは含みません。

依存はVeryl stdのみです。clock frequencyとbaud rateはparameter、frameは1 start bit・8 data bit・1 stop bitです。`valid`は受信byteの1-cycle pulse、framing errorは現行回路の動作（出力を抑止）に従います。物理`rx`入力の同期化は利用者のCDC契約です。追加の二重同期化は行いません。

```veryl
inst uart: uart::UartRx #( CLOCK_HZ: 50_000_000, BAUD_RATE: 115_200 ) (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
