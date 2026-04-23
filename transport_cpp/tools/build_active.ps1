#!/usr/bin/env pwsh
<#
.SYNOPSIS
Build script pour VS Code: compile le fichier actif du projet transport_cpp.
.PARAMETER ActiveFile
Nom du fichier actif (main.cpp, etude10_main.cpp, traces_main.cpp).
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ActiveFile
)

$ErrorActionPreference = 'Stop'

# Déterminer le répertoire transport_cpp (supposé être le répertoire parent du script)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$transportDir = Split-Path -Parent $scriptDir

# Créer le dossier bin
New-Item -ItemType Directory -Path "$transportDir\bin" -Force | Out-Null

$gpp = 'C:\msys64\ucrt64\bin\g++.exe'
$srcDir = "$transportDir\src"
$includeDir = "$transportDir\include"
$binDir = "$transportDir\bin"

# Déterminer la cible selon le fichier actif
switch ($ActiveFile) {
    'main.cpp' {
        $outputExe = "$binDir\transport_cli.exe"
        $sourceFiles = @(
            "$srcDir\main.cpp",
            "$srcDir\transport_problem.cpp",
            "$srcDir\generator.cpp"
        )
        Write-Host "Building: transport_cli.exe"
    }
    'etude10_main.cpp' {
        $outputExe = "$binDir\transport_etude10.exe"
        $sourceFiles = @(
            "$srcDir\etude10_main.cpp",
            "$srcDir\transport_problem.cpp",
            "$srcDir\generator.cpp"
        )
        Write-Host "Building: transport_etude10.exe"
    }
    'traces_main.cpp' {
        $outputExe = "$binDir\transport_traces.exe"
        $sourceFiles = @(
            "$srcDir\traces_main.cpp",
            "$srcDir\transport_problem.cpp",
            "$srcDir\generator.cpp"
        )
        Write-Host "Building: transport_traces.exe"
    }
    default {
        throw "Fichier actif non supporté: $ActiveFile. Utilisez main.cpp, etude10_main.cpp ou traces_main.cpp."
    }
}

# Compiler
Write-Host "Compiling with: $gpp -O3 -std=c++20 -I'$includeDir' $($sourceFiles -join ' ') -o '$outputExe'"
& $gpp -O3 -std=c++20 -I"$includeDir" $sourceFiles -o "$outputExe"

if ($LASTEXITCODE -ne 0) {
    throw "Compilation failed with exit code $LASTEXITCODE"
}

Write-Host "Build successful: $outputExe"
