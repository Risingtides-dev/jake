# Define the path to your batch file
$scriptPath = Join-Path $PSScriptRoot "run_external_tiktoks.bat"

# Define the alias name
$aliasName = "run external tiktoks"

# Create the alias (use Global scope)
Set-Alias -Name $aliasName -Value $scriptPath -Scope Global -Force

# Add the alias to your PowerShell profile for persistence
$profilePath = $PROFILE.CurrentUserAllHosts

if (-not (Test-Path $profilePath)) {
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
}

$aliasCommand = "Set-Alias -Name '$aliasName' -Value '$scriptPath' -Scope Global -Force"

# Check if the alias command already exists in the profile
if ((Get-Content $profilePath) -notcontains $aliasCommand) {
    Add-Content -Path $profilePath -Value "`n$aliasCommand"
    Write-Host "Alias '$aliasName' added to your PowerShell profile."
} else {
    Write-Host "Alias '$aliasName' already exists in your PowerShell profile."
}

Write-Host "You can now type '$aliasName' in new PowerShell sessions to run all external campaigns."
Write-Host "To use it immediately, run: .$profilePath"

