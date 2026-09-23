# v0.5.2 Release Notes

Chrome側の接続不良通知が発火しないことがある問題を修正しました。

## Fixed

Manifest V3 のService Workerはアイドル時に終了・再起動されます。
v0.5.1では接続失敗回数をメモリ上だけで保持していたため、
Service Worker再起動を挟むと失敗回数がリセットされ、
3回連続失敗の通知条件へ到達しない場合がありました。

v0.5.2では以下を修正しています。

- `pluginState` をService Worker起動時に `chrome.storage.local` から復元
- `consecutiveFailures` をService Worker再起動後も継続
- `alerted` を継続し、同一障害の通知連打を防止
- 復旧判定も保存状態を使うため、Service Worker再起動後でも復旧通知可能
- `sent / accepted / monitoring / lastHealth` 等も既存保存状態から継続

## Expected behavior

航海日誌改を停止して艦これタブを残した場合:

1. heartbeat失敗 1回目
2. heartbeat失敗 2回目
3. heartbeat失敗 3回目（約90秒）
4. Chrome通知を1回表示

航海日誌改を再起動すると復旧通知を1回表示します。
