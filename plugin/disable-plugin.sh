#!/usr/bin/env bash
set -eu
LOGBOOK="${LOGBOOK_DIR:-$HOME/logbook-kai}"
SRC="$LOGBOOK/plugins/kancolle-cdp-bridge-poc-v03.jar"
DST="$LOGBOOK/plugins/kancolle-cdp-bridge-poc-v03.jar.disabled"

if [ ! -f "$SRC" ]; then
  echo "有効なPoCプラグインは見つかりません: $SRC"
  exit 0
fi

if [ -e "$DST" ]; then
  echo "退避先が既に存在するため何も変更しません: $DST"
  exit 1
fi

mv "$SRC" "$DST"
echo "PoCプラグインを削除せず無効化しました:"
echo "$DST"
echo "航海日誌改を再起動してください。"
