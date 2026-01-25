$WshShell = New-Object -ComObject WScript.Shell

# Mënyrë më e sigurtë për të gjetur Desktop-in (edhe nëse është në OneDrive)
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Holkos Fatura.lnk"

# Përdorim lokacionin aktual të projektit
$ProjectDir = Get-Location
$MainScript = Join-Path $ProjectDir "main.py"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$MainScript`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Hap aplikacionin Holkos Fatura"
$Shortcut.Save()

Write-Host "Lokacioni i Desktop-it: $DesktopPath"
Write-Host "Lokacioni i Projektit: $ProjectDir"
Write-Host "Shortcut-i u krijua me sukses!"
