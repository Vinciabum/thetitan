@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════╗
echo  ║    MONOLOGUE  —  Agent            ║
echo  ╚═══════════════════════════════════╝
echo.

:: 가상환경 확인
if not exist ".venv\Scripts\activate.bat" (
    echo  [!] 가상환경이 없습니다. setup.bat 을 먼저 실행하세요.
    pause
    exit /b 1
)

:: .env 확인
if not exist ".env" (
    echo  [!] .env 파일이 없습니다. setup.bat 을 먼저 실행하세요.
    pause
    exit /b 1
)

echo  [*] 에이전트 시작 중...
echo  [*] 종료하려면 Ctrl+C 를 누르세요.
echo.

call .venv\Scripts\activate.bat
python main.py
