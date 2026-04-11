@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════╗
echo  ║      MONOLOGUE  —  Setup          ║
echo  ╚═══════════════════════════════════╝
echo.

:: .env 파일 확인
if not exist ".env" (
    echo  [!] .env 파일이 없습니다.
    echo      .env.example 을 복사한 뒤 API 키를 채워주세요.
    echo.
    copy .env.example .env >nul
    echo  [+] .env 파일을 생성했습니다. 편집 후 다시 실행하세요.
    pause
    exit /b 1
)

:: Python 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo  [!] Python이 설치되어 있지 않습니다.
    echo      https://www.python.org 에서 설치 후 다시 실행하세요.
    pause
    exit /b 1
)

:: 가상환경 생성
if not exist ".venv" (
    echo  [*] 가상환경 생성 중...
    python -m venv .venv
    echo  [+] .venv 생성 완료
) else (
    echo  [+] 기존 .venv 재사용
)

:: 패키지 설치
echo.
echo  [*] 패키지 설치 중... (시간이 걸릴 수 있습니다)
.venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [!] 패키지 설치 실패. 오류를 확인하세요.
    pause
    exit /b 1
)

echo.
echo  [+] 설치 완료!
echo.
echo  다음 명령어로 실행하세요:
echo    run_dashboard.bat   — 대시보드 실행
echo    run_agent.bat       — 에이전트 실행
echo.
pause
