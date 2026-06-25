@echo off
set "REPO_ROOT=%~dp0..\.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "TOOL_ROOT=D:\tools"
set "GIT_ROOT=%TOOL_ROOT%\git"
set "GIT_CONFIG_DIR=%TOOL_ROOT%\gitconfig"
set "CACHE_ROOT=%TOOL_ROOT%\cache"

if not exist "%GIT_ROOT%\cmd\git.exe" (
  echo Missing required local tool: %GIT_ROOT%\cmd\git.exe
  exit /b 1
)
if not exist "%GIT_ROOT%\bin\bash.exe" (
  echo Missing required local tool: %GIT_ROOT%\bin\bash.exe
  exit /b 1
)
if not exist "%REPO_ROOT%\.venv\Scripts\python.exe" (
  echo Missing required local tool: %REPO_ROOT%\.venv\Scripts\python.exe
  exit /b 1
)

if not exist "%GIT_CONFIG_DIR%" mkdir "%GIT_CONFIG_DIR%"
if not exist "%TOOL_ROOT%\home" mkdir "%TOOL_ROOT%\home"
if not exist "%CACHE_ROOT%\pip" mkdir "%CACHE_ROOT%\pip"
if not exist "%CACHE_ROOT%\pytest" mkdir "%CACHE_ROOT%\pytest"
if not exist "%CACHE_ROOT%\npm" mkdir "%CACHE_ROOT%\npm"
if not exist "%CACHE_ROOT%\uv" mkdir "%CACHE_ROOT%\uv"
if not exist "%REPO_ROOT%\.cao_agent_context" mkdir "%REPO_ROOT%\.cao_agent_context"

set "STOCK_BOT_REPO=%REPO_ROOT%"
set "STOCK_BOT_TOOLS=%TOOL_ROOT%"
set "GIT_CONFIG_GLOBAL=%GIT_CONFIG_DIR%\.gitconfig"
set "HOME=%TOOL_ROOT%\home"
set "USERPROFILE=%HOME%"
set "PIP_CACHE_DIR=%CACHE_ROOT%\pip"
set "PYTEST_ADDOPTS=-o cache_dir=%CACHE_ROOT:\=/%/pytest"
set "NPM_CONFIG_CACHE=%CACHE_ROOT%\npm"
set "UV_CACHE_DIR=%CACHE_ROOT%\uv"
set "STOCK_BOT_AGENT_CONTEXT=%REPO_ROOT%\.cao_agent_context"
set "PATH=%GIT_ROOT%\cmd;%GIT_ROOT%\bin;%GIT_ROOT%\usr\bin;%REPO_ROOT%\.venv\Scripts;%PATH%"

if "%STOCK_BOT_WRITE_GIT_CONFIG%"=="1" (
  set "SAFE_DIR=%REPO_ROOT:\=/%"
  git config --global --get-all safe.directory | findstr /x /c:"%SAFE_DIR%" >nul
  if errorlevel 1 git config --global --add safe.directory "%SAFE_DIR%"
  for /f "delims=" %%V in ('git config --global --get core.autocrlf 2^>nul') do set "GLOBAL_AUTOCRLF=%%V"
  if not "%GLOBAL_AUTOCRLF%"=="false" git config --global core.autocrlf false
  for /f "delims=" %%V in ('git -C "%REPO_ROOT%" config --local --get core.autocrlf 2^>nul') do set "LOCAL_AUTOCRLF=%%V"
  if not "%LOCAL_AUTOCRLF%"=="false" git -C "%REPO_ROOT%" config --local --replace-all core.autocrlf false
)

echo stock-bot local environment ready
echo Repo: %REPO_ROOT%
echo Tools: %TOOL_ROOT%
git --version
bash --version | findstr /n "^" | findstr "^1:"
python --version
