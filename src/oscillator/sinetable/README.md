# Sin wave table ROM生成用Pythonスクリプト

Sinの第一象限を1024サンプルでhexファイルに出力
分解能は31bit

## 実行

```shell
uv run main.py
```

## 生成されるファイル

- sine_data.txt: sinerom.verylのmem変数にコピーすること
