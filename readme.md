# Recherche opérationnelle

Projet réorganisé par type de contenu.

## Structure

- `scripts/` : scripts Python, étude 10, benchmark, interface et structure.
- `data/input/` : problèmes de transport de référence.
- `data/generated/` : fichiers temporaires créés par les générations et campagnes.
- `results/benchmark/` : CSV et graphiques du benchmark Python.
- `results/etude_10/` : CSV et exports de l'étude 10 Python.
- `docs/` : documentation et fichiers annexes.
- `transport_cpp/` : version C++ autonome, avec ses propres `results/`.

## Lancement rapide

- `python .\scripts\benchmark.py`
- `python .\scripts\etude_10.py`
- `python .\scripts\analyse_benchmark.py`
- `python .\scripts\interface.py`

## Données et résultats

Les problèmes de référence sont dans `data/input/`. Les fichiers temporaires créés par les scripts sont écrits dans `data/generated/`. Les sorties des analyses Python sont rangées dans `results/`.