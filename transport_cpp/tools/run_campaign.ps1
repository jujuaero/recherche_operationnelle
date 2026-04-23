param(
    [int]$Repetitions = 100,
    [int[]]$Stages = @(100, 400, 1000),
    [switch]$RunTraces,
    [int]$GroupId = 2,
    [int]$TeamId = 4
)

$ErrorActionPreference = 'Stop'

Push-Location "$PSScriptRoot\.."
try {
    if (-not (Test-Path ".\bin\transport_etude10.exe")) {
        throw "Executable manquant: .\bin\transport_etude10.exe. Compilez d'abord le projet C++."
    }

    foreach ($nMax in $Stages) {
        Write-Host "`n=== Stage n_max=$nMax, repetitions=$Repetitions ==="
        & ".\bin\transport_etude10.exe" $Repetitions $nMax
        if ($LASTEXITCODE -ne 0) {
            throw "Echec transport_etude10.exe (n_max=$nMax)."
        }
    }

    if ($RunTraces) {
        if (-not (Test-Path ".\bin\transport_traces.exe")) {
            throw "Executable manquant: .\bin\transport_traces.exe."
        }
        Write-Host "`n=== Generation des traces ==="
        & ".\bin\transport_traces.exe" $GroupId $TeamId "results/traces"
        if ($LASTEXITCODE -ne 0) {
            throw "Echec transport_traces.exe"
        }
    }

    if (Test-Path ".\tools\analyse_etude10.py") {
        Write-Host "`n=== Analyse maxima/complexite ==="
        python ".\tools\analyse_etude10.py"
    }

    Write-Host "`n[OK] Campagne terminee."
}
finally {
    Pop-Location
}
