@echo off
setlocal
pushd "%~dp0" || exit /b 1
python "%~dp0download_builds.py" %*
set "download_exit_code=%errorlevel%"
popd
exit /b %download_exit_code%
