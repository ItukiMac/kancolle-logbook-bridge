#!/usr/bin/env bash
set -eu

VERSION="${VERSION:-1.0.0}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
LOGBOOK="${LOGBOOK_DIR:-$HOME/logbook-kai}"
APP_JAR="$LOGBOOK/logbook-kai.jar"
PLUGINS="$LOGBOOK/plugins"
OUT="$PLUGINS/klb-logbook-plugin.jar"

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

cat > "$BUILD/MANIFEST.MF" <<EOF
Manifest-Version: 1.0
Implementation-Title: KLB Logbook Plugin
Implementation-Vendor: ItukiMac
Implementation-Version: $VERSION
Bundle-License: MIT
EOF

mkdir -p "$PLUGINS"

(
  cd "$BUILD/classes"
  "$JAR" --create \
    --file "$BUILD/klb-logbook-plugin-v$VERSION.jar" \
    --manifest "$BUILD/MANIFEST.MF" \
    .
)

cp -a "$BUILD/klb-logbook-plugin-v$VERSION.jar" "$OUT"

echo
echo "OK: プラグインを新規配置しました"
echo "$OUT"
echo
echo "旧バージョンのKLB/Direct Bridgeプラグインが残っている場合は同時に有効化しないでください。"
echo "航海日誌改を再起動してください。"
