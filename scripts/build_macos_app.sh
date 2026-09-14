#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="CampusJob-Agent"
APP_BUNDLE="${PROJECT_DIR}/dist/${APP_NAME}.app"
CONTENTS="${APP_BUNDLE}/Contents"
MACOS="${CONTENTS}/MacOS"
RESOURCES="${CONTENTS}/Resources"

echo "==> 1. 清理并初始化 .app 目录结构..."
rm -rf "${PROJECT_DIR}/dist"
mkdir -p "${MACOS}" "${RESOURCES}"

echo "==> 2. 生成高清应用图标..."
uv run python3 "${PROJECT_DIR}/generate_icon.py"
iconutil -c icns "${PROJECT_DIR}/build/icon.iconset" -o "${RESOURCES}/AppIcon.icns"

echo "==> 3. 写入 macOS 标准 Info.plist 属性字典..."
cat << 'PLIST' > "${CONTENTS}/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>zh_CN</string>
    <key>CFBundleDisplayName</key>
    <string>CampusJob-Agent</string>
    <key>CFBundleExecutable</key>
    <string>CampusJob-Agent</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.campusjob.agent</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>CampusJob-Agent</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.1.0</string>
    <key>CFBundleVersion</key>
    <string>1.1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
</dict>
</plist>
PLIST

echo "==> 4. 生成可执行启动文件..."
cat << LAUNCHER > "${MACOS}/CampusJob-Agent"
#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/local/bin:\$HOME/.local/bin:\$PATH"
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
CANDIDATE_ROOT="\$(cd "\${SCRIPT_DIR}/../../../.." && pwd)"

if [ -f "\${CANDIDATE_ROOT}/desktop.py" ]; then
    APP_ROOT="\${CANDIDATE_ROOT}"
else
    APP_ROOT="\${CANDIDATE_ROOT}"
fi

LOG_DIR="\$HOME/Library/Logs/CampusJob-Agent"
mkdir -p "\${LOG_DIR}"
LOG_FILE="\${LOG_DIR}/app.log"

exec >> "\${LOG_FILE}" 2>&1
echo "=== 启动时间: \$(date '+%Y-%m-%d %H:%M:%S') ==="
echo "APP_ROOT: \${APP_ROOT}"

# 寻找项目运行环境
if [ -f "\${APP_ROOT}/.venv/bin/python3" ]; then
    PYTHON_EXEC="\${APP_ROOT}/.venv/bin/python3"
    cd "\${APP_ROOT}"
    exec "\${PYTHON_EXEC}" "\${APP_ROOT}/desktop.py"
elif command -v uv >/dev/null 2>&1; then
    cd "\${APP_ROOT}"
    exec uv --directory "\${APP_ROOT}" run python3 "\${APP_ROOT}/desktop.py"
else
    PYTHON_EXEC="\$(command -v python3)"
    cd "\${APP_ROOT}"
    exec "\${PYTHON_EXEC}" "\${APP_ROOT}/desktop.py"
fi
LAUNCHER

chmod +x "${MACOS}/CampusJob-Agent"

echo "==> 5. 创建便携一键启动脚本..."
cat << 'SH_RUN' > "${PROJECT_DIR}/run_desktop.sh"
#!/usr/bin/env bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🚀 正在拉起 CampusJob-Agent 桌面战备系统..."
uv --directory "${PROJECT_DIR}" run python3 "${PROJECT_DIR}/desktop.py"
SH_RUN
chmod +x "${PROJECT_DIR}/run_desktop.sh"

echo "✅ 打包完成！macOS 桌面应用程序已生成于: ${APP_BUNDLE}"
