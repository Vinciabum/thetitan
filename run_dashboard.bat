@echo off
chcp 65001 >nul
echo.
echo  ╔═══════════════════════════════════╗
echo  ║    MONOLOGUE  —  Dashboard        ║
echo  ╚═══════════════════════════════════╝
echo.
echo  [*] 대시보드 서버 시작 중...
echo  [*] 브라우저에서 http://localhost:8501/dashboard.html 로 접속하세요.
echo  [*] 종료하려면 Ctrl+C 를 누르세요.
echo.

start "" "http://localhost:8501/dashboard.html"
python -m http.server 8501
