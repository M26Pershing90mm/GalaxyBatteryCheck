$ErrorActionPreference = 'Stop'
$folder = Split-Path -Parent $MyInvocation.MyCommand.Path
$launcher = Join-Path $folder 'galaxy battery check.pyw'
$icon = Join-Path $folder 'galaxy battery check.ico'
if (-not (Test-Path -LiteralPath $launcher)) { throw 'galaxy battery check.pyw not found.' }
if (-not (Test-Path -LiteralPath $icon)) { throw 'galaxy battery check.ico not found.' }
$desktop = [Environment]::GetFolderPath('Desktop')
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path $desktop 'Galaxy Battery Check.lnk'))
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $folder
$shortcut.IconLocation = "$icon,0"
$shortcut.Description = 'Galaxy Battery Check (Unofficial) - Read-only ADB Battery Information'
$shortcut.Save()
Write-Host "Created: $(Join-Path $desktop 'Galaxy Battery Check.lnk')"
