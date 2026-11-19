# Windows (main): run the progress sync every hour at :05 via Task Scheduler.
# Run in this folder:  powershell -ExecutionPolicy Bypass -File install_windows.ps1
# (ASCII only on purpose, so it works in both Windows PowerShell 5 and PowerShell 7)
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
python -m pip install -q -r "$dir\requirements.txt"
$py = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python).Source }
$action = New-ScheduledTaskAction -Execute $py -Argument "`"$dir\sync.py`" --role windows" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName "DiscordCourseProgress-Windows" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "OK: Task Scheduler now has 'DiscordCourseProgress-Windows' (every hour at :05)."
