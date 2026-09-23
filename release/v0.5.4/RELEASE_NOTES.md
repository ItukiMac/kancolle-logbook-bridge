# v0.5.4 Release Notes

Linux Mint / MATE で航海日誌改側の障害通知が短時間で消える問題を調整しました。

## Changed

- 障害通知 (critical): `notify-send --expire-time=0`
  - 通知デーモンが対応している場合、ユーザーが閉じるまで表示
- 復旧通知 (normal): `notify-send --expire-time=10000`
  - 10秒で消える従来動作

Chrome側通知ロジックとheartbeat監視ロジックに変更はありません。
