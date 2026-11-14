#requires -Version 5.1
[CmdletBinding()]
param(
    [switch]$EngineOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$engineRoot = Join-Path $repositoryRoot 'engine'
$projectRoot = Join-Path $PSScriptRoot 'Arcadia'
$logRoot = Join-Path $projectRoot 'Logs'
$pythonPath = Join-Path $engineRoot '.venv\Scripts\python.exe'
$gamePath = Join-Path $projectRoot 'Builds\Arcadia\Arcadia.exe'
$baseUrl = 'http://127.0.0.1:8000'

function Test-EngineHealth {
    try {
        $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 2
        return $health.estado -eq 'ok' -and -not [string]::IsNullOrWhiteSpace([string]$health.version)
    }
    catch { return $false }
}

function Test-LocalPort {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $connection = $client.BeginConnect('127.0.0.1', 8000, $null, $null)
        if (-not $connection.AsyncWaitHandle.WaitOne(500)) { return $false }
        $client.EndConnect($connection)
        return $true
    }
    catch { return $false }
    finally { $client.Dispose() }
}

try {
    if (Test-EngineHealth) {
        Write-Host "Motor disponible en $baseUrl; se reutiliza la instancia activa." -ForegroundColor Green
    }
    else {
        if (Test-LocalPort) {
            throw "El puerto local 8000 esta ocupado, pero /health no responde como npc-nav. Revisa ese servicio y vuelve a intentar; el lanzador no lo detendra."
        }
        if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
            throw "No existe $pythonPath. Prepara el entorno indicado en engine/README.md. Este lanzador no instala dependencias."
        }

        Push-Location -LiteralPath $engineRoot
        try {
            $checkOutput = & $pythonPath -c 'import uvicorn; from npc_nav.api.main import app' 2>&1
            $checkExitCode = $LASTEXITCODE
        }
        finally { Pop-Location }
        if ($checkExitCode -ne 0) {
            throw "El entorno Python no puede importar la API. Revisa engine/README.md (extra [api]). Detalle: $($checkOutput -join [Environment]::NewLine)"
        }

        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
        $stdoutPath = Join-Path $logRoot "engine-$stamp.stdout.log"
        $stderrPath = Join-Path $logRoot "engine-$stamp.stderr.log"
        $server = Start-Process -FilePath $pythonPath `
            -ArgumentList @('-m', 'uvicorn', 'npc_nav.api.main:app', '--host', '127.0.0.1', '--port', '8000', '--no-access-log') `
            -WorkingDirectory $engineRoot -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath

        [ordered]@{
            processId = $server.Id
            startedUtc = $server.StartTime.ToUniversalTime().ToString('o')
            executable = $pythonPath
            baseUrl = $baseUrl
            stdout = $stdoutPath
            stderr = $stderrPath
        } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'launcher-engine.json') -Encoding UTF8

        Write-Host "Iniciando motor Python (PID $($server.Id))..."
        $deadline = [DateTime]::UtcNow.AddSeconds(30)
        $ready = $false
        do {
            if (Test-EngineHealth) { $ready = $true; break }
            $server.Refresh()
            if ($server.HasExited) {
                $detail = if (Test-Path -LiteralPath $stderrPath) { (Get-Content -LiteralPath $stderrPath -Tail 12) -join [Environment]::NewLine } else { '' }
                throw "El motor termino antes de estar listo. Log: $stderrPath`n$detail"
            }
            Start-Sleep -Milliseconds 250
        } while ([DateTime]::UtcNow -lt $deadline)

        if (-not $ready) {
            throw "El motor no respondio en 30 segundos (PID $($server.Id)). Revisa $stderrPath. El proceso se deja disponible para diagnostico."
        }
        Write-Host "Motor listo. Logs: $logRoot" -ForegroundColor Green
    }

    $maps = @(Invoke-RestMethod -Uri "$baseUrl/mapas" -Method Get -TimeoutSec 5)
    if (@($maps | Where-Object { $_.nombre -eq 'den011d' }).Count -eq 0) {
        throw "La API responde pero no ofrece den011d. Revisa el dataset del motor activo en $baseUrl."
    }

    if ($EngineOnly) {
        Write-Host "Abre el proyecto $projectRoot en Unity Hub, carga Assets/Arcadia/Scenes/ArcadiaGarden.unity y pulsa Play."
        exit 0
    }

    if (-not (Test-Path -LiteralPath $gamePath -PathType Leaf)) {
        Write-Warning "Todavia no existe el ejecutable: $gamePath"
        Write-Host "El motor ya esta listo. Para jugar desde el Editor:"
        Write-Host "  1. Abre $projectRoot desde Unity Hub (Unity 6000.6.7f1)."
        Write-Host '  2. Carga Assets/Arcadia/Scenes/ArcadiaGarden.unity y pulsa Play.'
        Write-Host '  3. Para generar el ejecutable, usa el menu Arcadia > Compilar Windows.'
        exit 2
    }

    # The game is interactive and intentionally opens a visible window.
    Start-Process -FilePath $gamePath -WorkingDirectory (Split-Path -Parent $gamePath) | Out-Null
    Write-Host 'Arcadia abierto. Elige tus personajes y pulsa Iniciar recorrido.' -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "No se pudo iniciar Arcadia: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
