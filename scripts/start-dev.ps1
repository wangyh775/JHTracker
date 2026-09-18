# JHTracker 开发启动脚本 (PowerShell - 全量编译版)
$ErrorActionPreference = "Stop"

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "    JHTracker 智能求职管理平台 - 开发者全量编译启动    " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

Write-Host "[1/3] 正在全量编译前端最新静态资源 (tsc && vite build)..." -ForegroundColor Yellow
Push-Location "frontend"
npm run build
Pop-Location

Write-Host "[2/3] 设置环境并启动 JHTracker 一体化服务 (端口: 8000)..." -ForegroundColor Yellow
$env:PYTHONPATH = "backend"

Write-Host ""
Write-Host "-------------------------------------------------------" -ForegroundColor Green
Write-Host "访问网址: http://localhost:8000" -ForegroundColor Green
Write-Host "API 文档: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "开发提示: 若进行高频 UI 调试，可在 frontend 运行 npm run dev 享受毫秒级热重载" -ForegroundColor DarkGray
Write-Host "按 Ctrl + C 可终止服务" -ForegroundColor Green
Write-Host "-------------------------------------------------------" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:8000"
python backend\src\main.py
