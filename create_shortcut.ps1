$WshShell = New-Object -ComObject WScript.Shell

# Gjetja e saktë e Desktop-it dhe Projektit si string
$DesktopPath = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::Desktop)
$ShortcutPath = Join-Path $DesktopPath "Holkos Fatura.lnk"
$ProjectDir = (Get-Location).Path

$MainScript = Join-Path $ProjectDir "main.py"

try {
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "pythonw.exe"
    $Shortcut.Arguments = "`"$MainScript`""
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.IconLocation = "pythonw.exe,0"
    $Shortcut.Save()
    Write-Host "---"
    Write-Host "Sukses!"
    Write-Host "Desktop: $DesktopPath"
    Write-Host "Projekt: $ProjectDir"
} catch {
    Write-Host "Gabim: $($_.Exception.Message)"
}
