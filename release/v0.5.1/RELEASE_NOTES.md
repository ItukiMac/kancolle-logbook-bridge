# v0.5.1 Release Notes

v0.5.0 の heartbeat 監視開始判定を修正しました。

## Fixed

- 通常のDirect Bridge通信が流れているのに `/health` が
  `chrome=waiting heartbeatAge=-1` のままになる問題を修正
- Chrome側はトップレベルURLだけでなく、実際のCDP attach状態を
  heartbeat監視開始の根拠にするよう変更
- CDP attach成功時に即座に `active=true` heartbeatを送信
- Plugin側は通常の `/ingest` 成功もChrome生存確認として扱い、
  watchdogを自動的に `connected` へarmするよう変更

## Expected health state

艦これ通信が流れている状態では、例えば以下になります。

```text
OK received=... accepted=... api=... image=... json=... errors=0 chrome=connected heartbeatAge=...
```

## Existing v0.5 functionality

- Chrome側 `/ingest` 失敗の即時通知
- heartbeat 3回連続失敗（約90秒）でChrome通知
- Plugin側 90秒heartbeat断でLinux `notify-send`
- 復旧時の1回通知
- `active=false` による意図的監視解除
