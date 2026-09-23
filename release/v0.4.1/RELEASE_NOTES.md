# v0.4.1 Release Notes

v0.4.0 Chrome拡張のService Worker登録失敗を修正したメンテナンスリリースです。

## Fixed

- `background.js` のテンプレートリテラルに混入していた不要なバックスラッシュを削除
- Chromeで `Service worker registration failed. Status code: 15` となる問題を修正
- Release前に `node --check` で拡張JavaScriptの構文検証を実行するCIチェックを追加

## Included

v0.4.0で追加した以下のMessageFlow互換機能をそのまま含みます。

- `/kcs2/resources/ship/`
- `/kcs2/resources/map/`
- `/kcs2/resources/gauge/`
- `/kcs2/img/common/`
- `/kcs2/img/duty/`
- `/kcs2/img/sally/`
- 画像Base64復元
- JSON転送
- HTTP status / MIME type保持
- plugin manifest metadata
