$ErrorActionPreference = 'Stop'
python -m pytest
& "$PSScriptRoot\build.ps1"
Get-FileHash .\dist\LearningSiteLauncher.exe -Algorithm SHA256 | ForEach-Object { "$($_.Hash.ToLower())  LearningSiteLauncher.exe" } | Set-Content .\dist\LearningSiteLauncher.exe.sha256
