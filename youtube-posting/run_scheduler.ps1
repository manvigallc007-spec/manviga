# YouTube Posting Pipeline — Windows Task Scheduler Wrapper
# Runs every 6 hours via Windows Task Scheduler
# Last updated: 2026-03-29

$ErrorActionPreference = "Stop"

# ============================================================================
# PROJECT SETUP
# ============================================================================

$ProjectRoot = "C:\Users\sport\Manviga\youtube-posting"
$VenvPath = "C:\Users\sport\Manviga\.venv\Scripts\Activate.ps1"
$PipelineScript = "$ProjectRoot\src\run_pipeline.py"
$LogDir = "$ProjectRoot\logs"

# Create log directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SchedulerLog = "$LogDir\scheduler_${Timestamp}.log"

# ============================================================================
# LOGGING FUNCTION
# ============================================================================

function Log-Message {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] $Message"
    Write-Host $logEntry
    Add-Content -Path $SchedulerLog -Value $logEntry -Encoding UTF8
}

# ============================================================================
# ACTIVATE VENV & RUN PIPELINE
# ============================================================================

try {
    Log-Message "================================"
    Log-Message "YOUTUBE PIPELINE SCHEDULER START"
    Log-Message "================================"
    Log-Message "Project Root: $ProjectRoot"
    Log-Message "Pipeline Script: $PipelineScript"
    
    # Activate virtual environment
    Log-Message "Activating virtual environment..."
    & $VenvPath
    
    # Run the pipeline
    Log-Message "Running YouTube pipeline..."
    Set-Location $ProjectRoot
    python "$PipelineScript"
    
    Log-Message "✅ Pipeline completed successfully"
    Log-Message "================================"
}
catch {
    Log-Message "❌ ERROR: $_"
    Log-Message "Error occurred at line: $($_.InvocationInfo.ScriptLineNumber)"
    Log-Message "================================"
    exit 1
}
