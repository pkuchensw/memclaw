@echo off
chcp 65001 >nul
REM Task1 测试脚本 - 支持多种运行模式

echo ============================================
echo OpenClaw-MemBench Task1 测试脚本
echo ============================================
echo.

REM 检查参数
if "%1"=="" goto :help

if "%1"=="api" goto :run_api
if "%1"=="docker" goto :run_docker
if "%1"=="openclaw-docker" goto :run_openclaw_docker
if "%1"=="help" goto :help

echo 未知参数: %1
goto :help

:run_api
    echo [模式] API 模式 - 直接调用 API
echo.
    cd OpenClaw-MemBench
    python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime api
    goto :end

:run_docker
    echo [模式] Docker 模式 - 在 Docker 容器中运行 API 调用
echo.
    cd OpenClaw-MemBench
    python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime docker
    goto :end

:run_openclaw_docker
    echo [模式] OpenClaw-Docker 模式 - 真实 OpenClaw 环境
echo.
    cd OpenClaw-MemBench
    python eval/run_batch.py --category 01_Recent_Constraint_Tracking --max-tasks 1 --runtime openclaw-docker
    goto :end

:help
    echo 用法: test_task1.bat [模式]
echo.
    echo 可用模式:
    echo   api            - 直接调用 API (需要配置 API 密钥)
    echo   docker         - 在 Docker 容器中运行 API 调用
    echo   openclaw-docker - 使用真实 OpenClaw Docker 环境 (推荐)
echo.
    echo 示例:
    echo   test_task1.bat openclaw-docker
goto :end

:end
