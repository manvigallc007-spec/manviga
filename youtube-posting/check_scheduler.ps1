# ============================================================================
# YOUTUBE PIPELINE - TASK SCHEDULER STATUS CHECKER
# ============================================================================
# Check the status of the YouTube Pipeline scheduled task
# Last updated: 2026-03-29

$TaskName = "YouTubePostingPipeline"
$LogDir = "C:\Users\sport\Manviga\youtube-posting\logs"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "YouTube Pipeline Task Status" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if task exists
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if (-not $task) {
    Write-Host "❌ Task not found: $TaskName" -ForegroundColor Red
    Write-Host "Run setup_scheduler.ps1 as Administrator first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Task Found" -ForegroundColor Green
Write-Host ""

# Get task details
Write-Host "TASK INFORMATION:" -ForegroundColor Yellow
Write-Host "Task Name: $($task.TaskName)" -ForegroundColor White
Write-Host "State: $($task.State)" -ForegroundColor White
Write-Host "Description: $($task.Description)" -ForegroundColor White
Write-Host ""

# Get task history
Write-Host "RECENT EXECUTIONS:" -ForegroundColor Yellow
$taskHistory = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Host "Last Result: $($taskHistory.LastTaskResult)" -ForegroundColor White
Write-Host "Last Run Time: $($taskHistory.LastRunTime)" -ForegroundColor White
Write-Host "Next Run Time: $($taskHistory.NextRunTime)" -ForegroundColor White
Write-Host "Number of Misses: $($taskHistory.NumberOfMissedRuns)" -ForegroundColor White
Write-Host ""

# Show recent logs
Write-Host "RECENT LOGS:" -ForegroundColor Yellow
if (Test-Path $LogDir) {
    $recentLogs = Get-ChildItem -Path $LogDir -Filter "scheduler_*.log" -ErrorAction SilentlyContinue | `
                    Sort-Object LastWriteTime -Descending | Select-Object -First 5
    
    if ($recentLogs) {
        foreach ($log in $recentLogs) {
            Write-Host "  • $($log.Name) — $($log.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
        }
    } else {
        Write-Host "  (No log files yet)" -ForegroundColor Gray
    }
} else {
    Write-Host "  (Log directory not found)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "QUICK ACTIONS:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Run now:       Run-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "Edit task:     taskschd.msc" -ForegroundColor White
Write-Host "Enable task:   Enable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "Disable task:  Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host ""
