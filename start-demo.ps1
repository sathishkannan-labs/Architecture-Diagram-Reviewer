param([switch]$PythonOnly, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if ($PythonOnly) {
        if (-not (Test-Path '.venv\Scripts\python.exe')) {
            if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 -m venv .venv }
            else { & python -m venv .venv }
            if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ is required. Install Python, then retry.' }
        }
        & .\.venv\Scripts\python.exe -m pip install -e '.[test]'
        if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
        Write-Host 'Python-only demo: restricted validation requires Docker/Linux. Fixture review and ZIP download are available.'
        $headless = if ($NoBrowser) { 'true' } else { 'false' }
        & .\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --browser.gatherUsageStats=false "--server.headless=$headless"
        if ($LASTEXITCODE -ne 0) { throw 'Streamlit could not start.' }
    } else {
        if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
            throw 'Install/start Docker Desktop with Linux containers. For UI-only mode run: .\start-demo.ps1 -PythonOnly'
        }
        if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
        Write-Host 'For live extraction, set MODEL_API_KEY in .env before starting. Empty key supports fixtures.'
        & docker compose up --build -d
        if ($LASTEXITCODE -ne 0) { throw 'Docker build/start failed. Inspect docker compose logs; do not bypass the validator build gate.' }
        $ready = $false
        for ($i=0; $i -lt 30; $i++) {
            try {
                $response = Invoke-WebRequest 'http://127.0.0.1:8501/_stcore/health' -UseBasicParsing -TimeoutSec 1
                if ($response.StatusCode -eq 200) { $ready=$true; break }
            } catch {}
            Start-Sleep -Seconds 1
        }
        if (-not $ready) { throw 'UI health check failed. Inspect: docker compose logs' }
        Write-Host 'Demo ready at http://localhost:8501. Stop it with: docker compose down'
        if (-not $NoBrowser) { Start-Process 'http://localhost:8501' }
    }
} finally { Pop-Location }
