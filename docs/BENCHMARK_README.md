# Benchmark des Algorithmes de Transport

Script complet pour tester et analyser la complexité des algorithmes de transport.

## Structure

- `scripts/benchmark.py` : orchestration et exécution des tests.
- `scripts/analyse_benchmark.py` : analyse post-benchmark avec visualisations.
- `results/benchmark/resultats_benchmark.csv` : base de données des résultats.
- `results/benchmark/benchmark_temps.png` : graphe temps vs taille.
- `results/benchmark/benchmark_boites.png` : diagrammes en boîte.
- `results/benchmark/benchmark_cout_vs_temps.png` : nuage coût/temps.

## Utilisation

### Étude 3.3 du pire des cas

Pour générer les problèmes carrés, mesurer les temps CPU et tracer les nuages de points demandés par l'énoncé:

```powershell
python .\scripts\etude_10.py
```

Par défaut, le script exporte les résultats dans `results/etude_10/resultats_etude_10.csv` et sauvegarde les graphiques dans `results/etude_10/`.

### 1. Lancer une campagne de tests

```powershell
# Test rapide (100 itérations par config)
python .\scripts\benchmark.py 100

# Test complet (1000 itérations par config)
python .\scripts\benchmark.py 1000

# Par défaut (100)
python .\scripts\benchmark.py
```

Le script:
- Génère des problèmes aléatoires pour chaque configuration.
- Exécute les 4 algorithmes.
- Mesure le temps en millisecondes.
- Valide chaque solution.
- Sauvegarde incrémentalement dans `results/benchmark/resultats_benchmark.csv`.

Pendant l'exécution, le processus essaie automatiquement de se fixer sur un cœur performance sur Windows hybride.
Vous pouvez forcer le comportement via les variables d'environnement suivantes:
- `RO_CPU_CORE` : `auto` par défaut, ou un index de cœur logique précis.
- `RO_CPU_HIGH_PRIORITY` : mettre `1` pour passer le processus en priorité élevée.

Exemple sous PowerShell:

```powershell
$env:RO_CPU_CORE = "1"
$env:RO_CPU_HIGH_PRIORITY = "1"
python .\scripts\benchmark.py 100
```

### 2. Analyser les résultats

```powershell
python .\scripts\analyse_benchmark.py
```

Produit:
- Tableau de statistiques.
- Graphiques dans `results/benchmark/`.
- Synthèse exploitable dans Excel ou Python.

## Exemple d'utilisation

```python
import pandas as pd

df = pd.read_csv('results/benchmark/resultats_benchmark.csv')
df.groupby('algorithme')['temps_ms'].mean()
df.groupby(['n', 'm', 'algorithme'])['cout_total'].mean()
```

## Dépendances

```powershell
pip install pandas numpy matplotlib seaborn
```

## Notes

- Les résultats s'accumulent: relancer `benchmark.py` ajoute plus de données.
- Temps de execution: ~10-15 secondes par 100 tests.
- Avec 1000 tests × 6 configs × 3 algos = ~3h pour campagne complète.
