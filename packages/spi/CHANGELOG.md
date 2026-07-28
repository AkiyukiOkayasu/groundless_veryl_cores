# Changelog

## [Unreleased]

- 各testのdoc commentへmode別の検証対象を明記

### Changed

- 公開型packageをproject名と重複する`Spi`から`Types`へ改名
- `spi_pkg`を`Spi`へ改名し、SPI masterを独立packageへ移動
- `SpiMaster`へtransactionとMode 0〜3のedge契約を示すWavedromを追加
