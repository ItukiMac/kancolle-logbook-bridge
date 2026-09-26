# KLB Technical Notes

この文書は **KLB - KanColle Logbook Bridge** の技術情報です。一般ユーザー向けの導入手順は [README](../README.md) を参照してください。

## Architecture

```text
Google Chrome
  └─ KLB Chrome Extension
       └─ chrome.debugger / CDP
            ↓ localhost HTTP
          127.0.0.1:8891
            ↓
       KLB Logbook Plugin
            ↓
       logbook-kai ContentListenerSpi
            ↓
          航海日誌改
```

KLB は艦これサーバーへ追加の要求を送るためのツールではありません。Chrome が受信した通信をローカルで取得し、航海日誌改へ渡します。

## KLB Chrome Extension

Manifest V3 の Chrome 拡張です。

- 艦これの DMM タブへ `chrome.debugger` で接続
- iframe / OOPIF を自動追跡
- CDP Network domain から対象通信を取得
- API、画像、JSON を localhost の KLB Logbook Plugin へ送信
- 接続状態を heartbeat で監視

取得対象:

```text
/kcsapi/
/kcs2/resources/ship/
/kcs2/resources/map/
/kcs2/resources/gauge/
/kcs2/img/common/
/kcs2/img/duty/
/kcs2/img/sally/
```

## KLB Logbook Plugin

航海日誌改の Plugin API を使用します。

- `127.0.0.1:8891` のみで待受
- KLB パケットをデコード
- 画像 Base64 をバイナリへ復元
- Request / Response metadata を航海日誌改形式へ変換
- 既存の `ContentListenerSpi` へ渡す

航海日誌改本体の API / 画像解析処理は再実装しません。

## Bridge protocol

protocol v2 は request method / URI / query、POST data、response encoding、MIME type、HTTP status、response body を保持します。

旧 PoC との移行互換用に protocol v1 の decode も残しています。

## Monitoring

- heartbeat 間隔: 約30秒
- Plugin watchdog: 30秒
- ingest 失敗: 即時通知
- 接続断 / 復旧: Chrome と Plugin の双方で通知
- `GET http://127.0.0.1:8891/health` で状態確認可能

## Security / privacy

- Plugin listener は localhost のみ
- Cookie を KLB 側で保存・転送しない
- Chrome storage には診断用メタデータのみ保存
- `chrome.debugger` は強い権限なので、導入前にソース確認を推奨

## Naming

ユーザー向け名称:

- Product: **KLB - KanColle Logbook Bridge**
- Chrome component: **KLB Chrome Extension**
- logbook-kai component: **KLB Logbook Plugin**

互換性維持のため、Java package、内部 class 名、status element ID、TCP port 8891 など一部の内部識別子には旧名称が残っています。

## Additional documents

- [DESIGN.md](DESIGN.md): モジュール責務
- [OPERATIONS.md](OPERATIONS.md): KLBの運用
- [STATUS.md](STATUS.md): 実機検証状況
