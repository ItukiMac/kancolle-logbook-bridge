# v0.5.0 Release Notes

Chrome拡張と航海日誌改プラグインの接続不良を相互監視し、
ユーザーがログ取得停止に気付けるよう通知機能を追加しました。

## Added

### Chrome extension

- 艦これ監視中に30秒周期で `/heartbeat` を送信
- heartbeat 3回連続失敗（約90秒）でChrome通知
- `/ingest` 送信失敗は即時通知
- 接続復旧時に1回だけ復旧通知
- 艦これタブを閉じた場合や手動停止時は `active=false` を送信して監視解除
- ポップアップに監視ON/OFFと連続失敗回数を表示
- `alarms` / `notifications` 権限を追加

### logbook-kai plugin

- `POST /heartbeat` を追加
- Chrome状態を `waiting / connected / lost` で管理
- 90秒heartbeatが無い場合にLinux `notify-send` で通知
- 復旧時に1回だけ通知
- TCP/8891 bind失敗時も通知
- `/health` に `chrome=<state>` と `heartbeatAge=<seconds>` を追加
- heartbeat timeout計測は `System.nanoTime()` を使用し、通常のサスペンド時間をタイムアウトに含めない

## Existing functionality

- `/kcsapi/` direct forwarding
- MessageFlow-compatible `/kcs2/` image/JSON forwarding
- plugin metadata display
- localhost-only listener

## Verification requested

- Plugin停止時にChrome側通知が出ること
- Chrome/拡張停止時に航海日誌改側通知が出ること
- 復旧時に1回だけ通知されること
- 艦これタブを閉じた場合は異常通知されないこと
