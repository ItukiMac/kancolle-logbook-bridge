#!/usr/bin/env bash
set -euo pipefail

VERSION="${VERSION:-1.0.0}"
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

case "$WORK" in "$ROOT"/.release-build) ;; *) exit 1 ;; esac
case "$DIST" in "$ROOT"/dist) ;; *) exit 1 ;; esac

rm -rf "$WORK"
mkdir -p "$WORK/classes/META-INF/services" "$DIST"
cp "$ROOT/NOTICE.md" "$WORK/classes/META-INF/NOTICE.md"
cp "$ROOT/LICENSE" "$WORK/classes/META-INF/LICENSE"
rm -f "$DIST/"*

PLUGIN_SRC="$ROOT/plugin/src/local/kancolle/bridge/KancolleBridgeStartUp.java"
PLUGIN_NAME="kancolle-cdp-bridge-plugin-v$VERSION.jar"
PLUGIN_JAR="$DIST/$PLUGIN_NAME"
EXT_ZIP="$DIST/logbook-kai-cdp-bridge-extension-v$VERSION.zip"
FULL_ZIP="$DIST/logbook-kai-cdp-bridge-v$VERSION.zip"
NOTES="$ROOT/release/v$VERSION/RELEASE_NOTES.md"

javac -encoding UTF-8 -cp "$LOGBOOK_JAR" -d "$WORK/classes" "$PLUGIN_SRC"

printf '%s\n' 'local.kancolle.bridge.KancolleBridgeStartUp' \
  > "$WORK/classes/META-INF/services/logbook.plugin.lifecycle.StartUp"

cat > "$WORK/MANIFEST.MF" <<EOF
Manifest-Version: 1.0
Implementation-Title: KLB - KanColle Logbook Bridge
Implementation-Vendor: ItukiMac
Implementation-Version: $VERSION
Bundle-License: MIT
EOF

(
  cd "$WORK/classes"
  jar --create --file "$PLUGIN_JAR" --manifest "$WORK/MANIFEST.MF" .
)

(
  cd "$ROOT/extension"
  zip -qr "$EXT_ZIP" .
)

STAGE="$WORK/logbook-kai-cdp-bridge-v$VERSION"
mkdir -p "$STAGE/extension" "$STAGE/plugin"
cp -a "$ROOT/extension/." "$STAGE/extension/"
cp -a "$PLUGIN_JAR" "$STAGE/plugin/"
cp -a "$ROOT/README.md" "$ROOT/LICENSE" "$ROOT/NOTICE.md" "$ROOT/ACKNOWLEDGEMENTS.md" "$STAGE/"
[[ -f "$NOTES" ]] && cp -a "$NOTES" "$STAGE/RELEASE_NOTES.md"

cat > "$STAGE/plugin/install.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
LOGBOOK_DIR="\${LOGBOOK_DIR:-\$HOME/logbook-kai}"
SRC="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)/$PLUGIN_NAME"
DST="\$LOGBOOK_DIR/plugins/$PLUGIN_NAME"

mkdir -p "\$LOGBOOK_DIR/plugins"

if [[ -e "\$DST" ]]; then
  echo "NG: 既に存在します: \$DST" >&2
  echo "上書きしません。" >&2
  exit 1
fi

cp -a "\$SRC" "\$DST"
echo "OK: \$DST"
echo "旧バージョンのDirect Bridgeプラグインが残っている場合は同時に有効化しないでください。"
echo "航海日誌改を再起動してください。"
EOF

cat > "$STAGE/plugin/disable.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
LOGBOOK_DIR="\${LOGBOOK_DIR:-\$HOME/logbook-kai}"
SRC="\$LOGBOOK_DIR/plugins/$PLUGIN_NAME"
DST="\$SRC.disabled"

if [[ ! -f "\$SRC" ]]; then
  echo "有効なプラグインは見つかりません: \$SRC"
  exit 0
fi
if [[ -e "\$DST" ]]; then
  echo "退避先が既に存在するため変更しません: \$DST" >&2
  exit 1
fi
mv "\$SRC" "\$DST"
echo "無効化しました: \$DST"
echo "航海日誌改を再起動してください。"
EOF

chmod +x "$STAGE/plugin/install.sh" "$STAGE/plugin/disable.sh"

(
  cd "$WORK"
  zip -qr "$FULL_ZIP" "$(basename "$STAGE")"
)

(
  cd "$DIST"
  sha256sum \
    "$(basename "$FULL_ZIP")" \
    "$(basename "$EXT_ZIP")" \
    "$(basename "$PLUGIN_JAR")" \
    > "SHA256SUMS-v$VERSION.txt"
)

echo "Release files:"
ls -lh "$DIST"

python3 "$ROOT/scripts/verify-release-licenses.py" "$VERSION"
