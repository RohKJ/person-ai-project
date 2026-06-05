[CmdletBinding()]
param(
    [ValidateSet("help", "setup", "data", "db", "check", "test", "api", "dashboard", "all", "stop")]
    [string]$Task = "help"
)

$ErrorActionPreference = "Stop"
$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

function Write-Step {
    param([string]$Name)
    Write-Host ""
    Write-Host "==> $Name" -ForegroundColor Cyan
}

function Install-Dependencies {
    Write-Step "Installing Python dependencies"
    python -m pip install -r requirements.txt
}

function Generate-SampleData {
    Write-Step "Generating sample CSV data"
    python scripts/generate_sample_data.py
}

function Initialize-Database {
    Write-Step "Initializing SQLite database"
    python scripts/init_db.py
}

function Run-Checks {
    Write-Step "Compiling Python files"
    python -m compileall app dashboard scripts tests -q

    Write-Step "Running tests"
    python -m pytest
}

function Start-Api {
    Write-Step "Starting FastAPI on http://127.0.0.1:8000"
    python -m uvicorn app.main:app --reload
}

function Start-Dashboard {
    Write-Step "Starting Streamlit on http://127.0.0.1:8501"
    python -m streamlit run dashboard/Home.py
}

function Stop-LocalServers {
    Write-Step "Stopping local dev servers on ports 8000 and 8501"
    $connections = Get-NetTCPConnection -LocalPort 8000,8501 -ErrorAction SilentlyContinue
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

    if (-not $processIds) {
        Write-Host "No local dev server processes found."
        return
    }

    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "Stopping PID $processId ($($process.ProcessName))"
            Stop-Process -Id $processId -Force
        }
    }
}

function Show-Help {
    Write-Host "Usage:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File scripts/dev.ps1 <task>"
    Write-Host ""
    Write-Host "Tasks:"
    Write-Host "  setup      Install dependencies"
    Write-Host "  data       Generate sample CSV files"
    Write-Host "  db         Initialize SQLite database"
    Write-Host "  check      Compile Python files and run tests"
    Write-Host "  test       Run pytest"
    Write-Host "  api        Start FastAPI"
    Write-Host "  dashboard  Start Streamlit"
    Write-Host "  all        setup + data + db + check"
    Write-Host "  stop       Stop local servers on ports 8000 and 8501"
}

switch ($Task) {
    "setup" { Install-Dependencies }
    "data" { Generate-SampleData }
    "db" { Initialize-Database }
    "check" { Run-Checks }
    "test" {
        Write-Step "Running tests"
        python -m pytest
    }
    "api" { Start-Api }
    "dashboard" { Start-Dashboard }
    "all" {
        Install-Dependencies
        Generate-SampleData
        Initialize-Database
        Run-Checks
    }
    "stop" { Stop-LocalServers }
    default { Show-Help }
}
