# gndless_spi

SPI masterとSPI mode型を提供します。公開APIは`Spi::SpiMode`と`SpiMaster`です。

依存はVeryl stdのみです。CPOL/CPHAのMode 0〜3、`DATA_WIDTH`、`CLK_DIV`、busy/done、CS setup/hold、MISO同期化の責任は`SpiMaster`のdoc commentを参照してください。転送はstart受付からdoneまでの単一transactionで、busy中は入力を保持しません。

```veryl
inst spi: spi::SpiMaster::<spi::Spi::SpiMode::Mode0> (...);
```

検証: `veryl fmt --check && veryl check && veryl test && veryl build && veryl doc`。
