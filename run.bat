@echo off
docker rm -f karbhari >nul 2>&1
docker run -d --name karbhari --env-file backend\.env -p 8000:8000 karbhari:0.5.0
echo Running at http://127.0.0.1:8000
