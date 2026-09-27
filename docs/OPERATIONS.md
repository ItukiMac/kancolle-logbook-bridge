# KLBの運用

## 導入と起動

READMEの手順で拡張とPluginを導入し、航海日誌改とChromeを起動してください。
PluginのJARは航海日誌改のpluginsディレクトリに配置します。
同じPluginの複数バージョンを同時に有効にしないでください。

## 接続確認

拡張のポップアップで接続状態を確認してください。
データは同一PC内のHTTP接続でPluginへ送られます。
技術仕様と取得対象はDESIGN.mdを参照してください。

## 更新と無効化

航海日誌改を終了してからPluginを更新してください。
配布物のplugin/install.shは既存の配置先を上書きしません。
plugin/disable.shで無効化した後は航海日誌改を再起動してください。
拡張の更新後はChromeの拡張機能管理画面で再読み込みしてください。

## 開発時の公開検査

`publication-policy.json` は、製品ソースとPlugin JARのファイル許可一覧、およびレビュー済みメールアドレスを定義します。拡張とフルZIPの許可一覧は、このソース一覧から組み立てます。新しいファイルや第三者の権利表示を追加するときは、用途と必要なライセンスを確認して一覧も更新してください。正当な第三者表示は保持します。

PRとすべてのブランチ・タグへのpushで、ソース、取得済み全履歴の本文・識別情報、配布物を読み取り専用ジョブで検査します。PRでは提案されたheadコミットをcheckoutします。ローカルで実行する場合は、全履歴と対象refsを取得し、追加ファイルをGitのindexへ登録してから `python3 scripts/verify-publication.py` を実行してください。未知のメールは値を表示せず停止します。許可一覧の変更はレビューが必要です。これらのCI検査は、ブランチ保護による直接pushの制限を代替しません。

公開はmainの `release/RELEASE` が変更された場合だけ行います。検査とLinuxビルドの成功後、専用ジョブが既存タグ・公開済みリリース・ドラフトの不在を確認します。認証や通信に失敗した場合は停止します。検証済みコミットを指す新しいタグを作成し、新規ドラフトへアップロードした全アセットを再取得して、SHA-256と内容の検査に合格してから公開します。既存版の補修は新しい版として提供してください。

途中失敗では作成済みタグ・ドラフト・アセットを保持し、`publication-state` Actionsアーティファクトに段階と確認結果を記録します。書き込み結果が不明なら読み取りで照会し、自動の再試行・削除・上書きは行いません。状態を確認せずにジョブを再実行しないでください。既存タグまたはドラフトが残っていれば再実行も停止します。認証情報、検出したメールの値、ファイル本文は記録しません。

ローカルの検証コマンド:

```sh
python3 scripts/verify-publication.py
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
VERSION="$(cat release/RELEASE)" LOGBOOK_JAR=/path/to/logbook-kai.jar bash scripts/build-release.sh
python3 -O scripts/verify-release-licenses.py "$(cat release/RELEASE)"
```

公開APIの異常系テストにはモックを使用し、実リポジトリにテスト用リリースを作成しません。`LICENSE` と `NOTICE.md` の全文、入れ子の同一性、アーカイブのパス・重複・ファイル種別・CRC・チェックサムも検査します。
