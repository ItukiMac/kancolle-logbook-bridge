#!/usr/bin/env bash
set -eu

LOGBOOK="${LOGBOOK_DIR:-$HOME/logbook-kai}"
SRC="$LOGBOOK/plugins/klb-logbook-plugin.jar"
DST="$SRC.disabled"

if [ ! -f "$SRC" ]; then
  echo "有効な KLB Logbook Plugin は見つかりません: $SRC"
  exit 0
fi

if [ -e "$DST" ]; then
  echo "退避先が既に存在するため何も変更しません: $DST"
  exit 1
fi

mv "$SRC" "$DST"
echo "KLB Logbook Plugin を削除せず無効化しました:"
echo "$DST"
echo "航海日誌改を再起動してください。"
