# ClawMe Skill Maker 一键发布脚本
# 用法: .\scripts\release.ps1 [版本号]
# 示例: .\scripts\release.ps1 1.0.0

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Version
)

# 规范化版本号（确保有 v 前缀）
if (-not $Version.StartsWith("v")) { $Version = "v$Version" }

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

Write-Host "=== ClawMe Skill Maker 发布 $Version ===" -ForegroundColor Cyan
Write-Host ""

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host "错误: 存在未提交的更改，请先 commit" -ForegroundColor Red
    git status
    exit 1
}

# 检查是否在 main/master 分支
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -notmatch "^(main|master)$") {
    Write-Host "警告: 当前分支是 $branch，建议在 main 分支发布" -ForegroundColor Yellow
    $confirm = Read-Host "是否继续? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") { exit 1 }
}

Write-Host "1. 创建 Tag $Version..." -ForegroundColor Green
git tag -a $Version -m "Release $Version"

Write-Host "2. 推送到远程..." -ForegroundColor Green
git push origin $branch
git push origin $Version

Write-Host ""
Write-Host "发布完成! GitHub Actions 将自动构建 Release 和发布包。" -ForegroundColor Cyan
Write-Host "查看进度: https://github.com/gloweaseco-leo/clawme-skill-maker/actions"
