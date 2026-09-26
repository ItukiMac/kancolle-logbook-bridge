# v1.0.0 Release Notes

**KLB - KanColle Logbook Bridge** の正式初版です。

## Components

- **KLB Chrome Extension**
  - 艦これ通信を取得し、KLB Logbook Pluginへ送信
  - 接続状態を監視し、障害・復旧を通知
- **KLB Logbook Plugin**
  - localhost:8891 で受信
  - 航海日誌改へデータを引き渡し
  - 航海日誌改のメイン画面に KLB 状態を表示

## Release files

- `klb-v1.0.0.zip`
- `klb-chrome-extension-v1.0.0.zip`
- `klb-logbook-plugin-v1.0.0.jar`
- `SHA256SUMS-v1.0.0.txt`

## Branding

- 製品名を **KLB - KanColle Logbook Bridge** に統一
- Chrome側を **KLB Chrome Extension**
- 航海日誌改側を **KLB Logbook Plugin**
- 錨・通信・モニターを組み合わせた KLB アイコンを採用

## Compatibility

内部のJava package、プロトコル識別子、TCP/8891などは互換性維持のため変更していません。
