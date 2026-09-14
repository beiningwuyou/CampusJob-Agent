#!/usr/bin/env bash
# ==============================================================================
# CampusJob-Agent · 开源发布前安全与隐私脱敏检查看门狗
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_DIR}"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}🛡️  CampusJob-Agent 开源发布前安全审计与数据隔离检查${NC}"
echo -e "${BLUE}================================================================${NC}"

HAS_ERROR=0

# 1. 检查 .gitignore 是否存在且包含关键隔离规则
echo -e "\n${YELLOW}[1/5] 检查 .gitignore 隔离规则...${NC}"
if [ ! -f ".gitignore" ]; then
    echo -e "${RED}❌ 致命错误: 未找到 .gitignore 文件！${NC}"
    HAS_ERROR=1
else
    for pattern in "data/*" "*.db" ".env" "dist/" "build/"; do
        if ! grep -q "${pattern}" .gitignore; then
            echo -e "${RED}❌ 警告: .gitignore 中缺少关键规则: ${pattern}${NC}"
            HAS_ERROR=1
        fi
    done
    if [ ${HAS_ERROR} -eq 0 ]; then
        echo -e "${GREEN}✅ .gitignore 核心防御规则健全${NC}"
    fi
fi

# 2. 检查是否有本地私密数据/数据库被 git 意外跟踪
echo -e "\n${YELLOW}[2/5] 检查是否存在被误跟踪的本地敏感文件...${NC}"
if [ -d ".git" ]; then
    TRACKED_SECRETS=$(git ls-files | grep -E '\.env$|\.db$|\.sqlite$|\.wal$|data/resumes/[^.]|dist/|build/' || true)
    if [ -n "${TRACKED_SECRETS}" ]; then
        echo -e "${RED}❌ 拦截: 发现以下本地数据已被 git 追踪，请立即执行 git rm --cached 移出:${NC}"
        echo "${TRACKED_SECRETS}"
        HAS_ERROR=1
    else
        echo -e "${GREEN}✅ 暂存区无任何数据库、环境变量或大文件二进制${NC}"
    fi
else
    echo -e "${BLUE}ℹ️  当前目录尚未执行 git init，将在首次 commit 前生效${NC}"
fi

# 3. 扫描源码中的硬编码绝对路径与用户路径 (排除 pycache 与虚拟环境)
echo -e "\n${YELLOW}[3/5] 扫描源码与脚本中的作者个人绝对路径...${NC}"
PATH_LEAKS=$(grep -rnI --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=.pytest_cache --exclude-dir=.ruff_cache --exclude-dir=data -E '/Users/[a-zA-Z0-9_-]+' app scripts web tests desktop.py 2>/dev/null || true)
if [ -n "${PATH_LEAKS}" ]; then
    echo -e "${RED}❌ 发现个人绝对路径泄露:${NC}"
    echo "${PATH_LEAKS}"
    HAS_ERROR=1
else
    echo -e "${GREEN}✅ 源码与脚本中未发现任何个人绝对路径硬编码${NC}"
fi

# 4. 检查 .env.example 是否安全（确保不含真实 Key）
echo -e "\n${YELLOW}[4/5] 检查 .env.example 模板安全性...${NC}"
if [ -f ".env.example" ]; then
    if grep -qE "sk-[a-zA-Z0-9]{20,}" .env.example; then
        echo -e "${RED}❌ 拦截: .env.example 中包含疑似真实的 API Key！${NC}"
        HAS_ERROR=1
    else
        echo -e "${GREEN}✅ .env.example 模板安全合规${NC}"
    fi
else
    echo -e "${RED}❌ 缺少 .env.example 模板文件！${NC}"
    HAS_ERROR=1
fi

# 5. 检查开源规范文件
echo -e "\n${YELLOW}[5/5] 检查开源必备基础文件 (LICENSE / README / PRD)...${NC}"
for req_file in "README.md" "LICENSE" ".github/CONTRIBUTING.md" ".github/SECURITY.md" "docs/CampusJob_Agent_PRD_V1.0.md" "pyproject.toml"; do
    if [ ! -f "${req_file}" ]; then
        echo -e "${RED}❌ 缺少必要文件: ${req_file}${NC}"
        HAS_ERROR=1
    else
        echo -e "${GREEN}✅ 找到 ${req_file}${NC}"
    fi
done

echo -e "\n${BLUE}================================================================${NC}"
if [ ${HAS_ERROR} -eq 0 ]; then
    echo -e "${GREEN}🎉 恭喜！所有安全与脱敏检查均已通过，项目符合 GitHub 开源发布标准！${NC}"
    echo -e "${BLUE}================================================================${NC}"
    exit 0
else
    echo -e "${RED}🚨 安全审计未通过，请根据上方提示修复后再进行提交！${NC}"
    echo -e "${BLUE}================================================================${NC}"
    exit 1
fi
