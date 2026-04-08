# Benchmark des Algorithmes de Transport

Script complet pour tester et analyser la complexité de vos 4 algorithmes sur des milliers de cas aléatoires.

## 📊 Architecture

```
benchmark.py          → Orchestration et exécution des tests
analyse_benchmark.py  → Analyse post-benchmark avec visualisations
resultats_benchmark.csv  → Base de données des résultats (CSV + Pandas)
```

## 🚀 Utilisation

### Étude 3.3 du pire des cas

Pour générer les problèmes carrés, mesurer les temps CPU et tracer les nuages de points demandés par l'énoncé:

```bash
python etude_10.py
```

Par défaut, le script exécute 100 répétitions pour chaque valeur de `n`, exporte les résultats dans `resultats_etude_10.csv` et sauvegarde les graphiques dans `resultats_etude_10/`.

### 1. Lancer une campagne de tests

```bash
# Test rapide (100 itérations par config)
python benchmark.py 100

# Test complet (1000 itérations par config)
python benchmark.py 1000

# Par défaut (100)
python benchmark.py
```

Le script:
- ✅ Génère des problèmes aléatoires pour chaque configuration
- ✅ Exécute les 4 algorithmes (nord_ouest, balas_hammer, marche_pied)
- ✅ Mesure le temps en millisecondes
- ✅ Valide chaque solution
- ✅ Sauvegarde incrémentalement dans le CSV

Pendant l'exécution, le processus essaie automatiquement de se fixer sur un cœur performance sur Windows hybride.
Vous pouvez forcer le comportement via les variables d'environnement suivantes:
- `RO_CPU_CORE` : `auto` par défaut, ou un index de cœur logique précis si vous voulez forcer un cœur particulier
- `RO_CPU_HIGH_PRIORITY` : mettre `1` pour passer le processus en priorité élevée

Exemple sous PowerShell:

```powershell
$env:RO_CPU_CORE = "1"
$env:RO_CPU_HIGH_PRIORITY = "1"
python benchmark.py 100
```

Si vous ne définissez pas `RO_CPU_CORE`, le script tente de choisir automatiquement un cœur performance.

### 2. Analyser les résultats

```bash
python analyse_benchmark.py
```

Produit :
- 📈 Tableau de statistiques (temps moyen, écart-type, etc.)
- 📊 Graphiques (temps vs taille, distribution, etc.)
- 📋 Synthèse exportée en CSV pour Excel/R/Python

## 📋 Structure du CSV

| Colonne | Description |
|---------|-------------|
| `test_id` | Identifiant unique |
| `n` | Nombre de fournisseurs |
| `m` | Nombre de clients |
| `algorithme` | nord_ouest / balas_hammer / marche_pied |
| `temps_ms` | Temps d'exécution (ms) |
| `cout_total` | Coût de la solution trouvée |
| `base_size` | Nombre de cellules de base (doit être n+m-1) |
| `validations_ok` | Booléen: solution valide? |
| `timestamp` | Quand le test a été exécuté |

## 🔬 Exemple d'utilisation

```python
import pandas as pd

# Charger les résultats
df = pd.read_csv('resultats_benchmark.csv')

# Temps moyen par algo
df.groupby('algorithme')['temps_ms'].mean()

# Coût moyen par dimension et algo
df.groupby(['n', 'm', 'algorithme'])['cout_total'].mean()

# Filtrer: solutions valides seulement
df_valid = df[df['validations_ok'] == True]

# Plot rapid
import matplotlib.pyplot as plt
df[df['m']==5].groupby(['n', 'algorithme'])['temps_ms'].mean().unstack().plot()
plt.show()
```

## ⚙️ Configuration

Modifiez dans `benchmark.py`:

```python
configs = [
    (5, 5),
    (5, 10),
    (10, 5),
    (10, 10),
    (15, 15),
    (20, 20),
]
```

Ajoutez/supprimez les configurations (n×m) à tester.

## 📈 Interprétation des Résultats

### Temps moyen
- Plus bas = plus rapide
- Aide à identifier l'algorihtme le plus efficace

### Coût moyen
- Plus bas = meilleure solution
- Compare la qualité (pas tous les algos donnent le même coût)

### Base size
- Doit toujours être = n + m - 1
- Sinon : **BUG** ⚠️

### Validations ok
- Doit être 100% (ou très proche)
- Si < 100% : vérifier les contraintes

## 🛠️ Dépendances

```bash
pip install pandas numpy matplotlib seaborn
```

## 📝 Notes

- Les résultats s'accumulent: relancer `benchmark.py` ajoute plus de données
- Temps de execution: ~10-15 secondes par 100 tests
- Avec 1000 tests × 6 configs × 3 algos = ~3h pour campagne complète

## 🎯 Prochaines étapes

1. Lancez `benchmark.py 500` pour avoir assez de données
2. Gardez les configs petites (n,m ≤ 20) pour temps raisonnable
3. Exécutez `analyse_benchmark.py` avec les fichiers PNG
4. Utilisez les CSVs pour R/Jupyter/Excel
