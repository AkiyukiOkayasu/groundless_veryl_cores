# Agent Guidelines

## 応答・コメント

- ユーザーへの応答は日本語。doc/impl commentも日本語、識別子とport名は英語。
- 互換性維持は明示要求時のみ。不要なdead codeは削除する。

## プロジェクト固有

- `target/`と`doc/`の生成物、`dependencies/`のvendored stdlibは直接編集しない。
- `.veryl`編集後は、全編集を終えてから`veryl fmt` → `veryl check` → `veryl test`を実行し、`CHANGELOG.md`の`[Unreleased]`へ追記する。失敗時は修正して再実行する。
- releaseでは`Veryl.toml`のversionとCHANGELOGをtagに合わせ、clone後は`git config core.hooksPath .githooks`を設定する。
