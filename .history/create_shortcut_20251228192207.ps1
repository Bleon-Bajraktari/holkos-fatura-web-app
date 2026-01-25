$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.IO.Path]::Combine($env:USERPROFILE, "Desktop")
$ShortcutPath = Join-Path $DesktopPath "Holkos Fatura.lnk"
$ProjectDir = "C:\Users\Bleon\Desktop\Holkos Fatura First"
$MainScript = Join-Path $ProjectDir "main.py"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$MainScript`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Hap aplikacionin Holkos Fatura"
$Shortcut.Save()

Write-Host "Shortcut-i u krijua me sukses ne Desktop!"
