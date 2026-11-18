# Windows（主）：毎時 5 分に進み具合を更新する予定を「タスク スケジューラ」に入れる。
# このフォルダで PowerShell を開いて実行： powershell -ExecutionPolicy Bypass -File install_windows.ps1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
python -m pip install -q -r "$dir\requirements.txt"
$py = (Get-Command pythonw -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python).Source }
$action = New-ScheduledTaskAction -Execute $py -Argument "`"$dir\sync.py`" --role windows" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 1)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName "Discord講座 進み具合（Windows）" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "入れました。タスク スケジューラに「Discord講座 進み具合（Windows）」ができています。"
