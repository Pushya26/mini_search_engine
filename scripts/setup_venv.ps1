# Creates and bootstraps the Python virtual environment (Windows PowerShell).
# Usage: .\scripts\setup_venv.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "Creating virtual environment in .venv ..."
python -m venv .venv

Write-Host "Activating .venv ..."
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Upgrading pip ..."
python -m pip install --upgrade pip

Write-Host "Installing dependencies ..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

Write-Host ""
Write-Host "Done. Activate the venv with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
