# logbook-kai-cdp-bridge

Chrome DevTools の `logbook-kai` パネルや `logbook-kai-messageflow.jar` を常用せず、
Chrome の `chrome.debugger` / Chrome DevTools Protocol (CDP) で取得した艦これ API・画像・JSON通信を、
航海日誌改 (`logbook-kai`) のプラグインへ直接渡すためのブリッジです。

## 位置づけ

このリポジトリは、`logbook-kai` / `logbook-kai-messageflow` の運用を起点にした
**独立した派生・置換プロジェクト**です。

- `logbook-kai` 本体の fork ではありません。
- `logbook-kai` のソースコードやバイナリはこのリポジトリに含めません。
- `plugin/` は `logbook-kai` が公開しているプラグインAPIを利用するため、
  ビルド時・実行時に `logbook-kai` が必要です。
- `extension/` は `logbook-kai` のコードには依存しません。
- `logbook-kai-messageflow` は現在の実装のビルド時・実行時依存ではありません。
  従来の「Chrome → MessageFlow → 航海日誌改」という運用を置き換えるため、
  公開されている仕様・挙動・通信フローを参照しました。
- 現時点では upstream の実装コードをそのままコピーしたソースは含めていません。

したがって、本リポジトリ自身のライセンスは `LICENSE` に記載する ItukiMac の MIT License とし、
upstream は互換性・開発経緯の参照先として `ACKNOWLEDGEMENTS.md` に明記します。
将来 upstream のソースを取り込む場合は、その時点でライセンス表記を再確認します。

## Upstream / 参考プロジェクト

- 航海日誌改 (`logbook-kai`)
  - https://github.com/sakura0689/logbook-kai
  - 公開プラグインAPIを利用
- `logbook-kai-messageflow`
  - https://github.com/sakura0689/logbook-kai-messageflow
  - 従来の通信中継方式・運用フローの参考

本リポジトリは上記プロジェクトの公式配布物ではありません。

## 現在の構成

```text
Google Chrome (main profile)
  ↓ chrome.debugger / CDP
Chrome extension
  ↓ HTTP / localhost only
127.0.0.1:8891
  ↓
logbook-kai plugin
  ↓ ContentListenerSpi
航海日誌改
```

`logbook-kai-messageflow.jar` および TCP/8890 は通常運用では不要です。

## MessageFlow互換の取得対象

v0.4.0 では旧MessageFlowが扱っていた以下をDirect Bridgeで扱います。

```text
/kcsapi/
/kcs2/resources/ship/
/kcs2/resources/map/
/kcs2/resources/gauge/
/kcs2/img/common/
/kcs2/img/duty/
/kcs2/img/sally/
```

`/kcs2/` の画像はCDPからBase64形式で受け取りプラグイン側でバイナリへ復元し、
JSONはUTF-8テキストとして航海日誌改の既存 `ImageListener` へ渡します。
画像保存・スプライト分解は航海日誌改本体の既存処理を利用します。

## 現在確認できている状態

2026-09 時点の検証環境:

- Linux Mint 22.1 (MATE / X11)
- Google Chrome 153
- logbook-kai 25.0.8
- Java 24.0.1
- 艦これ本体の OOPIF / iframe に追従
- `/kcsapi/` の POST data / response body を取得
- Chrome → `127.0.0.1:8891` → logbook-kai plugin の直接連携
- `logbook-kai-messageflow.jar` を停止した状態で航海日誌改の更新を確認
- プラグイン受信口は localhost のみ
- Chrome を `--silent-debugger-extension-api` 付きで起動し、debugger 警告表示を抑止できることを確認
- v0.4.0で旧MessageFlow相当の `/kcs2/` 画像・JSON経路を実装

詳細は `docs/STATUS.md` を参照してください。

## ディレクトリ

```text
extension/          Chrome Manifest V3 拡張
plugin/             logbook-kai 用 Direct Bridge plugin
docs/STATUS.md      現時点の検証状況
docs/DESIGN.md      構成と責務
```

## ビルド / 導入

`plugin/build-and-install.sh` はデフォルトで `$HOME/logbook-kai/logbook-kai.jar` を
コンパイル時クラスパスとして参照し、生成したプラグインJARを
`$HOME/logbook-kai/plugins/` へ配置します。

Release版JARには以下のマニフェスト情報を付与します。

- Name: Kancolle CDP Bridge
- Vendor: ItukiMac
- Version: リリースバージョン
- License: MIT

Chrome側は `extension/` を `chrome://extensions` の
「パッケージ化されていない拡張機能を読み込む」から読み込みます。

## セキュリティ上の注意

- 艦これサーバーへ追加通信を送るための機能ではありません。
- Cookie は保存・転送しません。
- 履歴には POST 本文・レスポンス本文を保存しません。
- `chrome.debugger` は強い権限です。ソースを確認したうえで使用してください。
- `--silent-debugger-extension-api` は Chrome プロセス全体の debugger 警告を抑止します。
  将来的には管理ポリシーによる限定的な導入も検討対象です。

## License

MIT License. See `LICENSE`.
