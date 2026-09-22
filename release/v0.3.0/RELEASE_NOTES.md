# v0.3.0 Release Notes

初回の実用確認版です。

## Confirmed

- Chromeメインプロファイルで動作
- DevTools UI不要
- 艦これiframe/OOPIFへのCDP attach
- `/kcsapi/` POST/response body取得
- MessageFlowを経由せず `127.0.0.1:8891` へ直接転送
- logbook-kai 25.0.8の既存解析へ投入
- MessageFlow停止状態で航海日誌改の更新を確認
- `--silent-debugger-extension-api` によるChrome debugger警告抑止を確認

## Known limitations

- `/kcs2/` 画像/JSONの直接経路は未実装
- 複数PC配信/リプレイは未実装
- Chrome Web Store/ポリシー配布は未対応
- logbook-kai 25.0.8以外の互換性は未検証
