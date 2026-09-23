# v0.5.3 Release Notes

Chrome通知が表示されない問題を修正しました。

## Fixed

v0.5.2 では `chrome.notifications.create()` の `iconUrl` に
拡張同梱の SVG (`icon.svg`) を指定していましたが、
Chrome 153 / Linux 環境では通知生成時に

```text
Error: Unable to download all specified images.
```

となり、通知自体が作成されませんでした。

v0.5.3 では通知アイコンを埋め込みPNGの data URL に変更しました。

- `notifications` 権限はそのまま
- 外部画像取得なし
- 通知生成時のSVG読み込み失敗を回避
- 接続断/復旧通知のロジックはv0.5.2を継承
