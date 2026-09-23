# v0.4.0 Release Notes

旧 `logbook-kai-messageflow` が扱っていた `/kcs2/` 画像・JSON経路を Direct Bridge に追加しました。

## Added

- `/kcs2/resources/ship/`
- `/kcs2/resources/map/`
- `/kcs2/resources/gauge/`
- `/kcs2/img/common/`
- `/kcs2/img/duty/`
- `/kcs2/img/sally/`
- CDPのBase64画像レスポンスをプラグイン側でバイナリへ復元
- JSONレスポンスを航海日誌改の既存 `ImageListener` へ投入
- HTTP status / MIME typeをDirect Bridgeで保持
- `/health` に api/image/json カウンタ追加
- 航海日誌改のプラグイン一覧向けJARマニフェスト情報
  - Kancolle CDP Bridge
  - ItukiMac
  - version
  - MIT

## Compatibility

- Direct Bridge packet protocol v2を追加
- プラグイン側はv0.3拡張のprotocol v1も読み取り可能
- `logbook-kai-messageflow.jar` は不要

## User-side verification requested

- 航海日誌改 `resources/` への画像・JSON保存
- 艦娘画像・海域・ゲージ・任務関連リソースの取得
- プラグイン一覧の名称/ベンダー/バージョン/ライセンス表示
