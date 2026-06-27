#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="Replace Audio"
EXECUTABLE_NAME="ReplaceAudio"
APP_PATH="$ROOT_DIR/dist/$APP_NAME.app"
APP_ID="tv.argonautas.replaceaudio"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

cd "$ROOT_DIR"

if pgrep -x "$APP_NAME" >/dev/null 2>&1; then
  pkill -x "$APP_NAME" || true
  sleep 1
fi

rm -rf "$APP_PATH"
mkdir -p "$ROOT_DIR/build"
mkdir -p "$APP_PATH/Contents/MacOS" "$APP_PATH/Contents/Resources"

cp "$ROOT_DIR/replace_audio.py" "$APP_PATH/Contents/Resources/replace_audio.py"

cat > "$ROOT_DIR/build/ReplaceAudioLauncher.c" <<EOF
#include <errno.h>
#include <libgen.h>
#include <limits.h>
#include <mach-o/dyld.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static const char *first_existing_python(void) {
    const char *candidates[] = {
        "${PYTHON_BIN}",
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        NULL
    };
    for (int i = 0; candidates[i] != NULL; i++) {
        if (access(candidates[i], X_OK) == 0) {
            return candidates[i];
        }
    }
    return "python3";
}

int main(void) {
    char raw_path[PATH_MAX];
    uint32_t size = sizeof(raw_path);
    if (_NSGetExecutablePath(raw_path, &size) != 0) {
        fprintf(stderr, "Executable path is too long.\\n");
        return 1;
    }

    char resolved_path[PATH_MAX];
    if (realpath(raw_path, resolved_path) == NULL) {
        fprintf(stderr, "Cannot resolve executable path: %s\\n", strerror(errno));
        return 1;
    }

    char dir_buffer[PATH_MAX];
    strncpy(dir_buffer, resolved_path, sizeof(dir_buffer));
    dir_buffer[sizeof(dir_buffer) - 1] = '\\0';

    char script_path[PATH_MAX];
    snprintf(script_path, sizeof(script_path), "%s/../Resources/replace_audio.py", dirname(dir_buffer));

    const char *python = first_existing_python();
    char *const args[] = {(char *)python, script_path, NULL};
    execv(python, args);
    execvp(python, args);

    fprintf(stderr, "Cannot launch Python: %s\\n", strerror(errno));
    return 1;
}
EOF
clang "$ROOT_DIR/build/ReplaceAudioLauncher.c" -o "$APP_PATH/Contents/MacOS/$EXECUTABLE_NAME"

cat > "$APP_PATH/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>$EXECUTABLE_NAME</string>
  <key>CFBundleIdentifier</key>
  <string>$APP_ID</string>
  <key>CFBundleInfoDictionaryVersion</key>
  <string>6.0</string>
  <key>CFBundleName</key>
  <string>$APP_NAME</string>
  <key>CFBundleDisplayName</key>
  <string>$APP_NAME</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>CFBundleVersion</key>
  <string>1.0.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>10.15</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSHumanReadableCopyright</key>
  <string>© 2026 Argonautas</string>
</dict>
</plist>
EOF

echo "APPL????" > "$APP_PATH/Contents/PkgInfo"

/usr/bin/codesign --force --sign - "$APP_PATH" >/dev/null

if [[ "${1:-}" == "--verify" ]]; then
  /usr/bin/open -n "$APP_PATH"
  sleep 3
  pgrep -f "$APP_PATH/Contents/Resources/replace_audio.py" >/dev/null
  echo "$APP_NAME is running"
else
  echo "Built: $APP_PATH"
fi
