# v1.0.0 Release Notes

KLB (KanColle Logbook Bridge) の初版（first stable release）です。

## Branding

- 拡張機能名を **KLB - KanColle Logbook Bridge** に統一
- 艦これ → 航海日誌改の連携を表す錨・通信・モニターのKLBアイコンを採用
- 通知・ポップアップ・航海日誌改の状態表示もKLB表記へ統一

## Extension

- Manifest version: 1.0.0
- 通知アイコンは `extension/icon128.png` を使用
- Chrome通知の障害/復旧監視は従来どおり30秒基準
- `/kcsapi/` と対応する `/kcs2/` 画像/JSONを航海日誌改へ直接転送

## Plugin

- Plugin version: 1.0.0
- 航海日誌改の状態バーを `KLB:` 表記へ変更
- localhost:8891 のDirect Bridge互換プロトコルと既存運用パスは維持

## Compatibility

既存運用との互換性を優先し、以下の内部名・パスは変更しません。

- Repository: `logbook-kai-cdp-bridge`
- Plugin path: `$HOME/logbook-kai/plugins/kancolle-cdp-bridge.jar`
- Extension path: `$HOME/logbook-kai/cdp-bridge/extension/`
- Local endpoint: `127.0.0.1:8891`

v0.x系からの機能を整理し、v1.0.0を正式な初版として扱います。
