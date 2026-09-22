# Acknowledgements / 参考プロジェクト

## 航海日誌改 (logbook-kai)

https://github.com/sakura0689/logbook-kai

本プロジェクトの `plugin/` は、logbook-kai がプラグイン開発向けに公開している
`StartUp`, `ContentListenerSpi`, `RequestMetaData`, `ResponseMetaData` 等のAPIを利用します。
logbook-kai 本体のソースコードやバイナリは本リポジトリには含めません。

Upstream license: MIT License.

## logbook-kai-messageflow

https://github.com/sakura0689/logbook-kai-messageflow

本プロジェクトは、従来の Chrome Extension → MessageFlow → logbook-kai という
運用を置き換える目的から始まり、公開されている通信フロー・挙動を参考にしています。
現在の v0.3 系では MessageFlow はビルド時・実行時依存ではありません。

Upstream license: MIT License.

## ライセンス表記について

現時点の本リポジトリには、上記 upstream のソースコードまたはバイナリをコピーして
再配布している部分はありません。そのため upstream の著作権表示を本リポジトリの
`LICENSE` の著作権者として混在させず、互換性・開発経緯の参照先として本ファイルに記載しています。

将来 upstream のコードをコピー・改変して取り込む場合は、その変更に合わせて
該当する著作権表示とライセンス文を保持する必要があります。
