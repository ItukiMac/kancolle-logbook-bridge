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
- v0.4系で旧MessageFlow相当の `/kcs2/` 画像・JSON経路を実装・実機確認
- v0.5.0でChrome拡張と航海日誌改プラグインの相互監視・接続不良通知を追加

詳細は `docs/STATUS.md` を参照してください。

## ディレクトリ

```text
extension/          Chrome Manifest V3 拡張
plugin/             logbook-kai 用 Direct Bridge plugin
docs/STATUS.md      現時点の検証状況
docs/DESIGN.md      構成と責務
docs/OPERATIONS.md  Mint自動起動・バックアップ・OBS録画先確認
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

運用環境では固定パス `$HOME/logbook-kai/cdp-bridge/extension/`、
プラグインは固定名 `$HOME/logbook-kai/plugins/kancolle-cdp-bridge.jar`
を推奨します。

## 接続監視

Chrome拡張は、艦これタブを監視している間だけ30秒周期で
`127.0.0.1:8891/heartbeat`へheartbeatを送ります。

- Chrome側: `/ingest`失敗は即時通知、heartbeat確認失敗は最初の30秒チェックで通知
- Plugin側: heartbeatまたは正常なingestが30秒途絶えた場合に `notify-send` で通知
- 復旧時は双方で1回だけ復旧通知
- 艦これタブを閉じる/監視停止する場合は `active=false` で監視解除
- `/health` には `chrome=waiting|connected|lost` と `heartbeatAge` を表示

## 接続状態の常時表示

v0.6.0 では通知だけに依存せず、航海日誌改のメインウィンドウ上部に
Direct Bridge の状態ストリップを追加します。

表示例:

```text
Direct Bridge: 接続中 | HB 2秒 | API 6 / 画像 26 / JSON 13 | エラー 0
```

状態は `接続中 / 待機中 / 接続断` で表示されます。
航海日誌改本体のファイルは変更せず、Pluginが起動時にメインウィンドウへ
表示領域を追加する方式です。表示領域の追加に失敗した場合でも、
Chrome拡張ポップアップと `http://127.0.0.1:8891/health` で確認できます。

障害判定はv0.6.0から30秒を基準にします。
Chrome側は30秒周期のheartbeat確認で最初の失敗時に通知し、
Plugin側は最後のheartbeatまたは正常なingestから30秒で `lost` に遷移します。

## セキュリティ上の注意

- 艦これサーバーへ追加通信を送るための機能ではありません。
- Cookie は保存・転送しません。
- 履歴には POST 本文・レスポンス本文を保存しません。
- `chrome.debugger` は強い権限です。ソースを確認したうえで使用してください。
- `--silent-debugger-extension-api` は Chrome プロセス全体の debugger 警告を抑止します。
  将来的には管理ポリシーによる限定的な導入も検討対象です。

## License

MIT License. See `LICENSE`.
