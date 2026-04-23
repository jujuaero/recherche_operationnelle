# Transport C++

Réécriture C++ du projet de transport (algorithmes + étude 3.3) dans un dossier séparé.

## Contenu

- `transport_cli` : exécute les algorithmes sur un fichier ou un problème aléatoire.
- `transport_etude10` : benchmark/étude 3.3 unifié (`n = 10, 40, 100, 400, 1000, 4000, 10000`).
- `transport_traces` : génération automatique des traces demandées (12 problèmes, NO + BH).
- `results/etude10/` : sortie de l'étude 10 C++.
- `results/traces/` : traces générées par `transport_traces`.
- `results/traces_test/` : traces de test et archives de validation.
- `../data/input/` : problèmes d'entrée de référence utilisés par les traces.

## Build (PowerShell)

```powershell
cd transport_cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

Si `cmake` n'est pas installé, build direct avec `g++`:

```powershell
New-Item -ItemType Directory -Path .\bin -Force | Out-Null

g++ -O3 -std=c++20 -I".\include" .\src\main.cpp .\src\transport_problem.cpp .\src\generator.cpp -o .\bin\transport_cli.exe
g++ -O3 -std=c++20 -I".\include" .\src\etude10_main.cpp .\src\transport_problem.cpp .\src\generator.cpp -o .\bin\transport_etude10.exe
g++ -O3 -std=c++20 -I".\include" .\src\traces_main.cpp .\src\transport_problem.cpp .\src\generator.cpp -o .\bin\transport_traces.exe
```

## Exécution

CLI solveur:

```powershell
.\build\Release\transport_cli.exe random 10 10
# ou
.\build\Release\transport_cli.exe file ..\data\input\transport1.txt
```

Benchmark / Étude 3.3:

```powershell
.\build\Release\transport_etude10.exe 100
```

Optionnel: limiter les tailles jusqu'à `n_max` pour un run progressif:

```powershell
.\build\Release\transport_etude10.exe 100 1000
```

## Traces d'exécution (rendu)

Génération des 24 traces (12 problèmes x NO/BH) avec format de nom demandé:

```powershell
.\build\Release\transport_traces.exe 2 4 results\traces
```

Sortie exemple: `results\traces\2-4-trace5-no.txt`, `results\traces\2-4-trace5-bh.txt`.

## Campagne progressive et reprise

Script PowerShell prêt à l'emploi:

```powershell
.\tools\run_campaign.ps1 -Repetitions 100 -Stages 100,400,1000 -RunTraces -GroupId 2 -TeamId 4
```

Le script enchaîne les stages d'étude, génère les traces et lance l'analyse des maxima/classification.

Sortie: `results\etude10\resultats_etude10_cpp.csv`

## Remarques

- Le code Python d'origine est inchangé.
- Cette version C++ accélère fortement les boucles et réduit l'overhead Python.
- Les très grandes tailles (notamment `n=10000`) restent potentiellement coûteuses en mémoire et en temps selon la méthode d'optimisation.
