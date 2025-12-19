@echo off
rem Wrapper for QoreLogic Check running inside Docker

rem Ensure local ledger directory exists
if not exist "%USERPROFILE%\.qorelogic\ledger" mkdir "%USERPROFILE%\.qorelogic\ledger"

rem Run container with persistent ledger volume
docker run --rm -v "%CD%:/src" -v "%USERPROFILE%\.qorelogic\ledger:/app/ledger" -w /src qorelogic:latest -m qorelogic_gatekeeper.cli %*
