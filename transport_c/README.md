# Transport C (etude_10)

Version C pure et from-scratch de l'etude progressive inspiree de scripts/etude_10.py.

## Ce que fait le programme

- Genere des problemes carres equilibres pour plusieurs tailles `n`.
- Mesure les temps CPU suivants:
  - `theta_NO_s`: initialisation Nord-Ouest
  - `theta_BH_s`: initialisation Balas-Hammer
  - `t_NO_s`: optimisation marche-pied apres Nord-Ouest
  - `t_BH_s`: optimisation marche-pied apres Balas-Hammer
  - `theta_plus_t_NO_s`
  - `theta_plus_t_BH_s`
- Exporte les resultats dans `results/etude_10_c/resultats_etude_10_c.csv`.
- Exporte les maxima par taille/mesure dans `results/etude_10_c/maxima_temps.csv`.

## Build (PowerShell)

```powershell
cd transport_c
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j
```

## Execution

```powershell
./build/Release/transport_etude10_c.exe
```

Mode rapide (parite avec l'option Python):

```powershell
./build/Release/transport_etude10_c.exe --quick
```

## Note technique

- Pas de pont C/C++: les algorithmes sont implementes en C dans src/transport_core.c.
- Structures de donnees contigues pour limiter l'overhead memoire/cache.
- Compilation release agressive (O3/LTO et options platforme) pour maximiser la vitesse.

## Reproductibilite

Vous pouvez fixer la graine aleatoire:

```powershell
./build/Release/transport_etude10_c.exe --seed=12345
```
