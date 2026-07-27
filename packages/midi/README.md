# gndless_midi

MIDI速度のbyte receiverです。MIDI message parserではありません。公開APIは`MidiRx`です。

`uart` packageへ依存し、baud rateはMIDI規格の31,250に固定します。利用者が変更するparameterはsystem clock等に限定します。UARTの`valid`をそのままbyte pulseとして伝播し、同期化はUARTとMIDIで二重に追加しません。frame形式・latency・resetは`MidiRx` doc commentを正とします。

```veryl
inst midi: midi::MidiRx #( CLOCK_HZ: 50_000_000 ) (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
