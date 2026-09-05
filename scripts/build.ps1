$ErrorActionPreference = 'Stop'
python -m PyInstaller --noconfirm --clean launcher.spec
Write-Host "Built dist\LearningSiteLauncher.exe"
