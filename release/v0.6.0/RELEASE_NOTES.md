# v0.6.0 Release Notes

接続不良の検知時間を約30秒へ短縮し、通知以外でも通信状態を常時確認できるようにしました。

## Added

### 航海日誌改メインウィンドウの状態表示

航海日誌改本体を改造せず、Direct Bridge Pluginがメインウィンドウ上部へ
状態ストリップを追加します。

表示内容:

```text
Direct Bridge: 接続中 | HB 2秒 | API 6 / 画像 26 / JSON 13 | エラー 0
```

状態:
- 接続中
- 待機中
- 接続断

表示色も状態に応じて変更します。

### 非通知の確認手段

- 航海日誌改メインウィンドウの状態ストリップ
- Chrome拡張ポップアップ
- `http://127.0.0.1:8891/health`

## Changed

- Plugin側 heartbeat timeout: 90秒 → 30秒
- Plugin watchdog確認周期: 10秒 → 5秒
- Chrome側 heartbeat失敗通知: 3回連続失敗 → 最初の失敗で通知
- `/health` に `timeout=30` を追加

## Notes

Chromeのheartbeat確認自体は30秒周期です。
Plugin側は正常な `/ingest` 通信も生存確認として扱うため、
実際に艦これ通信が流れている間は状態表示も随時更新されます。
