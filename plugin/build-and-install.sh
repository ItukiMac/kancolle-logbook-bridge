#!/usr/bin/env bash
set -eu

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGBOOK="${LOGBOOK_DIR:-$HOME/logbook-kai}"
APP_JAR="$LOGBOOK/logbook-kai.jar"
PLUGINS="$LOGBOOK/plugins"
OUT="$PLUGINS/kancolle-cdp-bridge-poc-v03.jar"

if [ ! -f "$APP_JAR" ]; then
  echo "NG: $APP_JAR が見つかりません"
  exit 1
fi

if [ -e "$OUT" ]; then
  echo "NG: 既に存在します: $OUT"
  echo "上書きしません。"
  exit 1
fi

JAVAC="$(command -v javac || true)"
JAR="$(command -v jar || true)"

if [ -z "$JAVAC" ] || [ -z "$JAR" ]; then
  echo "NG: javac または jar が見つかりません。"
  exit 1
fi

BUILD="$ROOT/build"
rm -rf "$BUILD"
mkdir -p "$BUILD/classes/META-INF/services"
cp "$ROOT/../NOTICE.md" "$BUILD/classes/META-INF/NOTICE.md"
cp "$ROOT/../LICENSE" "$BUILD/classes/META-INF/LICENSE"

"$JAVAC" \
  -encoding UTF-8 \
  -cp "$APP_JAR" \
  -d "$BUILD/classes" \
  "$ROOT/src/local/kancolle/bridge/KancolleBridgeStartUp.java"

printf '%s\n' \
  'local.kancolle.bridge.KancolleBridgeStartUp' \
  > "$BUILD/classes/META-INF/services/logbook.plugin.lifecycle.StartUp"

mkdir -p "$PLUGINS"

(
  cd "$BUILD/classes"
  "$JAR" --create --file "$BUILD/kancolle-cdp-bridge-poc-v03.jar" .
)

cp -a "$BUILD/kancolle-cdp-bridge-poc-v03.jar" "$OUT"

echo
echo "OK: プラグインを新規配置しました"
echo "$OUT"
echo
echo "次: 航海日誌改を一度終了し、通常どおり起動し直してください。"
echo "既存MessageFlowは削除せず、そのままで構いません。"
