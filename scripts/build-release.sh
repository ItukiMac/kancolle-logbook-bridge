#!/usr/bin/env bash
set -euo pipefail

VERSION="${VERSION:-0.3.0}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGBOOK_JAR="${LOGBOOK_JAR:-$HOME/logbook-kai/logbook-kai.jar}"
WORK="$ROOT/.release-build"
DIST="$ROOT/dist"

if [[ ! -f "$LOGBOOK_JAR" ]]; then
  echo "NG: logbook-kai.jar が見つかりません: $LOGBOOK_JAR" >&2
  echo "LOGBOOK_JAR=/path/to/logbook-kai.jar を指定してください。" >&2
  exit 1
fi

for cmd in javac jar zip sha256sum; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "NG: $cmd が見つかりません" >&2
    exit 1
  }
done

case "$WORK" in
  "$ROOT"/.release-build) ;;
  *) echo "NG: 安全確認に失敗: WORK=$WORK" >&2; exit 1 ;;
esac

case "$DIST" in
  "$ROOT"/dist) ;;
  *) echo "NG: 安全確認に失敗: DIST=$DIST" >&2; exit 1 ;;
esac

rm -rf "$WORK"
mkdir -p "$WORK/classes/META-INF/services" "$DIST"
cp "$ROOT/NOTICE.md" "$WORK/classes/META-INF/NOTICE.md"
cp "$ROOT/LICENSE" "$WORK/classes/META-INF/LICENSE"

PLUGIN_SRC="$ROOT/plugin/src/local/kancolle/bridge/KancolleBridgeStartUp.java"
PLUGIN_JAR="$DIST/kancolle-cdp-bridge-plugin-v$VERSION.jar"
EXT_ZIP="$DIST/logbook-kai-cdp-bridge-extension-v$VERSION.zip"
FULL_ZIP="$DIST/logbook-kai-cdp-bridge-v$VERSION.zip"

javac   -encoding UTF-8   -cp "$LOGBOOK_JAR"   -d "$WORK/classes"   "$PLUGIN_SRC"

printf '%s\n'   'local.kancolle.bridge.KancolleBridgeStartUp'   > "$WORK/classes/META-INF/services/logbook.plugin.lifecycle.StartUp"

(
  cd "$WORK/classes"
  jar --create --file "$PLUGIN_JAR" .
)

(
  cd "$ROOT/extension"
  zip -qr "$EXT_ZIP" .
)

STAGE="$WORK/logbook-kai-cdp-bridge-v$VERSION"
mkdir -p "$STAGE/extension" "$STAGE/plugin"
cp -a "$ROOT/extension/." "$STAGE/extension/"
cp -a "$PLUGIN_JAR" "$STAGE/plugin/"
cp -a "$ROOT/plugin/disable-plugin.sh" "$STAGE/plugin/disable.sh"
cp -a "$ROOT/README.md" "$ROOT/LICENSE" "$ROOT/NOTICE.md" "$ROOT/ACKNOWLEDGEMENTS.md" "$STAGE/"

cat > "$STAGE/plugin/install.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
LOGBOOK_DIR="${LOGBOOK_DIR:-$HOME/logbook-kai}"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/kancolle-cdp-bridge-plugin-v0.3.0.jar"
DST="$LOGBOOK_DIR/plugins/$(basename "$SRC")"

mkdir -p "$LOGBOOK_DIR/plugins"

if [[ -e "$DST" ]]; then
  echo "NG: 既に存在します: $DST" >&2
  echo "上書きしません。" >&2
  exit 1
fi

cp -a "$SRC" "$DST"
echo "OK: $DST"
echo "航海日誌改を再起動してください。"
EOF
chmod +x "$STAGE/plugin/install.sh"

(
  cd "$WORK"
  zip -qr "$FULL_ZIP" "$(basename "$STAGE")"
)

(
  cd "$DIST"
  sha256sum     "$(basename "$FULL_ZIP")"     "$(basename "$EXT_ZIP")"     "$(basename "$PLUGIN_JAR")"     > "SHA256SUMS-v$VERSION.txt"
)

echo
echo "Release files:"
ls -lh   "$FULL_ZIP"   "$EXT_ZIP"   "$PLUGIN_JAR"   "$DIST/SHA256SUMS-v$VERSION.txt"

python3 "$ROOT/scripts/verify-release-licenses.py" "$VERSION"
