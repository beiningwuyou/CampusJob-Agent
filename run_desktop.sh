#!/usr/bin/env bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🚀 正在拉起 CampusJob-Agent 桌面战备系统..."
uv --directory "${PROJECT_DIR}" run python3 "${PROJECT_DIR}/desktop.py"
