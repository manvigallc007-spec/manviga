# ============================================================================
# YOUTUBE PIPELINE - WINDOWS TASK SCHEDULER SETUP
# ============================================================================
# Run this script as Administrator to create the scheduled task
# Last updated: 2026-03-29

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "YouTube Pipeline Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# CONFIGURATION
# ============================================================================

$TaskName = "YouTubePostingPipeline"
$BatchFile = "C:\Users\sport\Manviga\youtube-posting\run_scheduler.bat"
$Description = "YouTube Posting Pipeline - Runs every 6 hours (AI news > video generation > upload)"

# ============================================================================
# CHECK ADMIN PRIVILEGES
# ============================================================================

$isAdmin = [Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains [Security.Principal.SecurityIdentifier]"S-1-5-32-544"
if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Administrator privileges confirmed" -ForegroundColor Green
Write-Host ""

# ============================================================================
# CHECK IF BATCH FILE EXISTS
# ============================================================================

if (-not (Test-Path $BatchFile)) {
    Write-Host "❌ ERROR: Batch file not found: $BatchFile" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Batch file found: $BatchFile" -ForegroundColor Green
Write-Host ""

# ============================================================================
# REMOVE EXISTING TASK (IF ANY)
# ============================================================================

$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "⚠ Existing task found. Removing old task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "✓ Old task removed" -ForegroundColor Green
} else {
    Write-Host "✓ No existing task found" -ForegroundColor Green
}

Write-Host ""

# ============================================================================
# CREATE NEW SCHEDULED TASK
# ============================================================================

Write-Host "Creating new scheduled task..." -ForegroundColor Cyan

try {
    # Create trigger for every 6 hours starting now
    $startTime = (Get-Date).AddMinutes(1)
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 6) `
                                         -RepetitionDuration (New-TimeSpan -Days 36500) `
                                         -At $startTime

    # Create action to run batch file
    $action = New-ScheduledTaskAction -Execute $BatchFile

    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -MultipleInstances Parallel

    # Register the scheduled task with highest privileges
    $task = Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description $Description `
        -RunLevel Highest `
        -ErrorAction Stop

    Write-Host "✓ Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "TASK DETAILS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Task Name: $TaskName" -ForegroundColor White
    Write-Host "Frequency: Every 6 hours" -ForegroundColor White
    Write-Host "First Run: $(($startTime).ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
    Write-Host "Script: $BatchFile" -ForegroundColor White
    Write-Host "Run Level: Highest (Admin)" -ForegroundColor White
    Write-Host "Status: ENABLED" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Logs Location:" -ForegroundColor Green
    Write-Host "C:\Users\sport\Manviga\youtube-posting\logs\" -ForegroundColor White
    Write-Host ""

}
catch {
    Write-Host "❌ ERROR creating task: $_" -ForegroundColor Red
    exit 1
}

# ============================================================================
# VERIFY TASK CREATION
# ============================================================================

Write-Host "Verifying task creation..." -ForegroundColor Cyan
$verifyTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($verifyTask) {
    Write-Host "✓ Task verification successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Yellow
    Write-Host "1. Verify logs in: C:\Users\sport\Manviga\youtube-posting\logs\" -ForegroundColor Yellow
    Write-Host "2. Check Task Scheduler: taskschd.msc" -ForegroundColor Yellow
    Write-Host "3. Manually run with: Run-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "❌ Task verification failed!" -ForegroundColor Red
    exit 1
}
