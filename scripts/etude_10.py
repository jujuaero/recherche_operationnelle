"""Étude 3.3: complexité dans le pire des cas pour les algorithmes de transport.

Le script génère des problèmes carrés n x n, mesure les temps CPU des quatre
mesures demandées, exporte les résultats et produit les graphiques utiles pour
l'étude des nuages de points et des maxima.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from structure import ProblemeTransport


# Configuration progressive des tailles avec itérations adaptées
CONFIG_SIZES = {
    # Ancienne configuration conservée en référence :
    # 10: 100,
    # 40: 100,
    # 100: 100,
    # 400: 100,
    # 1000: 100,
    # 4000: 100,
    # 10000: 100,
    10: 100,
    30: 80,
    60: 60,
    100: 50,
    200: 30,
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = PROJECT_ROOT / "results" / "etude_10"
FICHIER_RESULTATS = RESULTS_DIR / "resultats_etude_10.csv"
DOSSIER_SORTIE = RESULTS_DIR
MAX_ITERATIONS_MARCHE_PIED = 5000


def _copier_probleme(probleme: ProblemeTransport) -> ProblemeTransport:
    copie = ProblemeTransport(probleme.n, probleme.m)
    copie.couts = [ligne[:] for ligne in probleme.couts]
    copie.provisions = probleme.provisions[:]
    copie.commandes = probleme.commandes[:]
    copie.transport = [[0] * probleme.m for _ in range(probleme.n)]
    copie.base = set()
    return copie


def generer_probleme_carre(n: int) -> ProblemeTransport:
    """Génère un problème de transport carré n x n selon l'énoncé."""
    couts = [[random.randint(1, 100) for _ in range(n)] for _ in range(n)]

    provisions = [0] * n
    commandes = [0] * n

    for i in range(n):
        for j in range(n):
            valeur = random.randint(1, 100)
            provisions[i] += valeur
            commandes[j] += valeur

    probleme = ProblemeTransport(n, n)
    probleme.couts = couts
    probleme.provisions = provisions
    probleme.commandes = commandes
    probleme.transport = [[0] * n for _ in range(n)]
    probleme.base = set()
    return probleme


def _mesurer_cpu(fonction):
    debut = time.process_time()
    fonction()
    fin = time.process_time()
    return fin - debut


def mesurer_une_realisation(probleme: ProblemeTransport) -> dict:
    """Mesure thetaNO, thetaBH, tNO et tBH sur un même problème."""
    resultat = {}

    prob = _copier_probleme(probleme)
    resultat["theta_NO_s"] = _mesurer_cpu(prob.methode_nord_ouest)

    prob = _copier_probleme(probleme)
    resultat["theta_BH_s"] = _mesurer_cpu(prob.methode_balas_hammer)

    prob = _copier_probleme(probleme)
    prob.methode_nord_ouest()
    resultat["t_NO_s"] = _mesurer_cpu(
        lambda: prob.methode_marche_pied_potentiels(
            methode_initiale="nord_ouest",
            max_iterations=MAX_ITERATIONS_MARCHE_PIED,
            initialisation_deja_faite=True,
        )
    )

    prob = _copier_probleme(probleme)
    prob.methode_balas_hammer()
    resultat["t_BH_s"] = _mesurer_cpu(
        lambda: prob.methode_marche_pied_potentiels(
            methode_initiale="balas_hammer",
            max_iterations=MAX_ITERATIONS_MARCHE_PIED,
            initialisation_deja_faite=True,
        )
    )

    resultat["theta_plus_t_NO_s"] = resultat["theta_NO_s"] + resultat["t_NO_s"]
    resultat["theta_plus_t_BH_s"] = resultat["theta_BH_s"] + resultat["t_BH_s"]
    return resultat


def executer_etude(config_sizes: dict = None) -> pd.DataFrame:
    """Exécute l'étude complète avec tailles et répétitions adaptées.
    
    Args:
        config_sizes: dict mapping {taille -> nb_repetitions}. 
                     Par défaut utilise CONFIG_SIZES global.
    """
    if config_sizes is None:
        config_sizes = CONFIG_SIZES
    
    lignes = []
    total_configs = len(config_sizes)
    
    print(f"\n{'='*80}")
    print(f"ÉTUDE DE COMPLEXITÉ PROGRESSIVE")
    print(f"{'='*80}")
    print(f"Configurations à tester: {total_configs}")
    print(f"Tailles: {sorted(config_sizes.keys())}\n")

    for idx, (n, nb_repetitions) in enumerate(sorted(config_sizes.items()), 1):
        print(f"\n[{idx}/{total_configs}] Taille n = {n:5d} ({nb_repetitions} répétitions)")
        
        for repetition in range(1, nb_repetitions + 1):
            try:
                probleme = generer_probleme_carre(n)
                mesures = mesurer_une_realisation(probleme)
                ligne = {
                    "n": n,
                    "repetition": repetition,
                    **mesures,
                }
                lignes.append(ligne)
            except Exception as e:
                print(f"  [ERREUR] Répétition {repetition}/{nb_repetitions}: {str(e)[:40]}")
                continue

            if repetition % max(1, nb_repetitions // 5) == 0:
                progress_pct = (repetition / nb_repetitions) * 100
                print(f"  Progression: {repetition}/{nb_repetitions} ({progress_pct:.0f}%)")

    df = pd.DataFrame(lignes)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(FICHIER_RESULTATS, index=False)
    print(f"\n[OK] {len(df)} résultats exportés vers {FICHIER_RESULTATS}")
    return df


def _melt_resultats(df: pd.DataFrame) -> pd.DataFrame:
    colonnes = [
        "theta_NO_s",
        "theta_BH_s",
        "t_NO_s",
        "t_BH_s",
        "theta_plus_t_NO_s",
        "theta_plus_t_BH_s",
    ]
    df_melt = df.melt(id_vars=["n", "repetition"], value_vars=colonnes, var_name="mesure", value_name="temps_s")
    return df_melt


def tracer_nuages(df: pd.DataFrame) -> None:
    """Trace les nuages de points pour chaque mesure."""
    df_melt = _melt_resultats(df)
    mesures = list(df_melt["mesure"].unique())

    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharex=True)
    axes = axes.flatten()

    for axe, mesure in zip(axes, mesures):
        subset = df_melt[df_melt["mesure"] == mesure]
        sns.scatterplot(data=subset, x="n", y="temps_s", ax=axe, alpha=0.55, s=20)
        axe.set_title(mesure)
        axe.set_xlabel("n")
        axe.set_ylabel("Temps CPU (s)")

    plt.tight_layout()
    DOSSIER_SORTIE.mkdir(exist_ok=True)
    chemin = DOSSIER_SORTIE / "nuages_points.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()


def tracer_maxima(df: pd.DataFrame) -> pd.DataFrame:
    """Trace les maxima par n pour chaque mesure et retourne la table agrégée."""
    df_melt = _melt_resultats(df)
    maxima = (
        df_melt.groupby(["n", "mesure"], as_index=False)["temps_s"]
        .max()
        .rename(columns={"temps_s": "temps_max_s"})
    )

    plt.figure(figsize=(12, 7))
    sns.lineplot(data=maxima, x="n", y="temps_max_s", hue="mesure", marker="o")
    plt.title("Maxima des temps CPU par taille")
    plt.xlabel("n")
    plt.ylabel("Temps CPU max (s)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    DOSSIER_SORTIE.mkdir(exist_ok=True)
    chemin = DOSSIER_SORTIE / "maxima_temps.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()

    maxima.to_csv(DOSSIER_SORTIE / "maxima_temps.csv", index=False)
    return maxima


def tracer_vues_benchmark(df: pd.DataFrame) -> None:
    """Ajoute des vues synthétiques inspirées du benchmark pour le rapport."""
    df_melt = _melt_resultats(df)

    # 1) Courbes de tendance (moyenne et dispersion) par n et mesure.
    plt.figure(figsize=(12, 7))
    sns.lineplot(
        data=df_melt,
        x="n",
        y="temps_s",
        hue="mesure",
        estimator="mean",
        errorbar="sd",
        marker="o",
    )
    plt.title("Tendance moyenne des temps CPU (style benchmark)")
    plt.xlabel("n")
    plt.ylabel("Temps CPU (s)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    DOSSIER_SORTIE.mkdir(exist_ok=True)
    chemin = DOSSIER_SORTIE / "benchmark_style_tendance.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()

    # 2) Boîtes à moustaches pour visualiser la variabilité par taille.
    focus = df_melt[df_melt["mesure"].isin(["theta_plus_t_NO_s", "theta_plus_t_BH_s"])]
    plt.figure(figsize=(12, 7))
    sns.boxplot(data=focus, x="n", y="temps_s", hue="mesure")
    plt.title("Distribution des temps complets par taille (style benchmark)")
    plt.xlabel("n")
    plt.ylabel("Temps CPU (s)")
    plt.grid(True, axis="y", alpha=0.25)
    plt.tight_layout()
    chemin = DOSSIER_SORTIE / "benchmark_style_boites.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()

    # 3) Trade-off NO vs BH sur les temps complets (points individuels).
    plt.figure(figsize=(10, 7))
    sns.scatterplot(
        data=df,
        x="theta_plus_t_NO_s",
        y="theta_plus_t_BH_s",
        hue="n",
        palette="viridis",
        alpha=0.7,
        s=35,
    )
    borne = max(df["theta_plus_t_NO_s"].max(), df["theta_plus_t_BH_s"].max())
    plt.plot([0, borne], [0, borne], linestyle="--", color="gray", linewidth=1)
    plt.title("Comparaison NO vs BH (temps complets)")
    plt.xlabel("theta + t avec initialisation Nord-Ouest (s)")
    plt.ylabel("theta + t avec initialisation Balas-Hammer (s)")
    plt.grid(True, alpha=0.25)
    plt.tight_layout()
    chemin = DOSSIER_SORTIE / "benchmark_style_tradeoff_no_vs_bh.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()


def imprimer_resume(maxima: pd.DataFrame) -> None:
    """Affiche un résumé simple des maxima observés."""
    print("\nRÉSUMÉ DES MAXIMA")
    print("=" * 80)
    for mesure in maxima["mesure"].unique():
        subset = maxima[maxima["mesure"] == mesure]
        ligne = subset.loc[subset["temps_max_s"].idxmax()]
        print(
            f"{mesure}: max={ligne['temps_max_s']:.6f} s pour n={int(ligne['n'])}"
        )


def main():
    """Exécute l'étude complète avec configuration progressive."""
    import sys
    
    config = CONFIG_SIZES.copy()
    
    # Optionnel: permettre de surcharger certaines tailles via CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Mode rapide pour tester: seulement petites et moyennes
        config = {k: v for k, v in config.items() if k <= 500}
        print("[INFO] Mode RAPIDE: seulement tailles <= 500")
    
    df = executer_etude(config_sizes=config)
    
    print(f"\n{'='*80}")
    print("GÉNÉRATION DES GRAPHIQUES")
    print(f"{'='*80}")
    
    tracer_nuages(df)
    maxima = tracer_maxima(df)
    tracer_vues_benchmark(df)
    imprimer_resume(maxima)
    
    print(f"\n[OK] Étude complète terminée !")


if __name__ == "__main__":
    main()