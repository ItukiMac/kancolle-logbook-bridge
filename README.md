# KLB - KanColle Logbook Bridge

KLB は、Google Chrome で動作する艦これと **航海日誌改 (logbook-kai)** を直接連携するための非公式ツールです。

## 構成要素

| コンポーネント | 役割 |
| --- | --- |
| **KLB Chrome Extension** | Chrome 上の艦これ通信を取得し、KLB Logbook Plugin へ渡します。 |
| **KLB Logbook Plugin** | 受け取ったデータを航海日誌改へ渡します。 |

通常利用では旧 `logbook-kai-messageflow.jar` は不要です。

## 導入

### 1. KLB Logbook Plugin

Release から `klb-logbook-plugin-v<version>.jar` を取得し、航海日誌改の `plugins` ディレクトリへ配置します。

推奨配置名:

```text
~/logbook-kai/plugins/klb-logbook-plugin.jar
```

旧版の `kancolle-cdp-bridge*.jar` が残っている場合は、同時に有効化しないでください。

### 2. KLB Chrome Extension

Release から `klb-chrome-extension-v<version>.zip` を展開します。

Chrome で `chrome://extensions/` を開き、

1. 「デベロッパー モード」を有効化
2. 「パッケージ化されていない拡張機能を読み込む」
3. 展開した KLB Chrome Extension のフォルダーを選択

これで導入完了です。

### 3. 動作確認

艦これと航海日誌改を起動し、航海日誌改の KLB 状態表示が **接続中** になることを確認してください。

## ドキュメント

技術仕様は README から分離しています。

- [技術仕様](docs/TECHNICAL.md)
- [設計](docs/DESIGN.md)
- [運用](docs/OPERATIONS.md)
- [検証状況](docs/STATUS.md)

## 免責

- 本プロジェクトは **艦隊これくしょん -艦これ-、DMM GAMES、航海日誌改の公式プロジェクトではありません**。
- Chrome の `debugger` 権限を使用します。内容を確認したうえで利用してください。
- Chrome、艦これ、航海日誌改などの更新により動作しなくなる可能性があります。
- 利用によって生じた損害について作者は保証しません。自己責任で利用してください。
- 本リポジトリのコードは [MIT License](LICENSE) で提供します。

## 関連プロジェクト

KLB は以下のプロジェクトと関係があります。

- [航海日誌改 (logbook-kai)](https://github.com/sakura0689/logbook-kai)  
  **KLB Logbook Plugin** は、航海日誌改が公開している Plugin API を利用します。KLB は航海日誌改の公式機能・forkではなく、航海日誌改本体も同梱しません。

- [logbook-kai-messageflow](https://github.com/sakura0689/logbook-kai-messageflow)  
  KLB は従来の `Chrome → MessageFlow → 航海日誌改` 構成を置き換える目的で開発され、公開されている通信フローや挙動を参考にしています。現在の KLB は MessageFlow をビルド時・実行時ともに必要としません。

両プロジェクトは MIT License で公開されています。
