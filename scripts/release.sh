#!/bin/bash
# ClawMe Skill Maker 一键发布脚本
# 用法: ./scripts/release.sh [版本号]
# 示例: ./scripts/release.sh 1.0.0

set -e
VERSION="$1"

if [ -z "$VERSION" ]; then
    echo "用法: $0 <版本号>"
    echo "示例: $0 1.0.0"
    exit 1
fi

# 规范化版本号
[[ "$VERSION" != v* ]] && VERSION="v$VERSION"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== ClawMe Skill Maker 发布 $VERSION ==="
echo ""

# 检查未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "错误: 存在未提交的更改，请先 commit"
    git status
    exit 1
fi

# 检查分支
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "main" && "$BRANCH" != "master" ]]; then
    echo "警告: 当前分支是 $BRANCH，建议在 main 分支发布"
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
fi

echo "1. 创建 Tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"

echo "2. 推送到远程..."
git push origin "$BRANCH"
git push origin "$VERSION"

echo ""
echo "发布完成! GitHub Actions 将自动构建 Release 和发布包。"
echo "查看进度: https://github.com/gloweaseco-leo/clawme-skill-maker/actions"
