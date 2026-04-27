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
import numpy as np

from structure import ProblemeTransport

CONFIG_SIZES = {}
current = 1
step = 1
max_key = 60
cpt = 0

while current <= max_key:
    CONFIG_SIZES[current] = 25
    current += step
    cpt += 1
    if cpt % 20 == 0:  # après 20 itérations avec le même pas, on l'augmente
        step = min(step + 1, 50)

print(CONFIG_SIZES)

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


def executer_etude(config_sizes: dict = None, mode: str = "nouveau") -> pd.DataFrame:
    """
    Exécute l'étude.
    Mode 'nouveau' : repart de zéro.
    Mode 'continuer' : charge le CSV existant et ajoute les nouvelles mesures.
    """
    if config_sizes is None:
        config_sizes = CONFIG_SIZES

    lignes = []

    # gestion de la reprise
    if mode == "continuer" and FICHIER_RESULTATS.exists():
        print(f"[INFO] Chargement des données existantes depuis {FICHIER_RESULTATS.name}...")
        df_existant = pd.read_csv(FICHIER_RESULTATS)
        lignes = df_existant.to_dict('records')
        # on identifie ce qui a déjà été fait (combinaison n et répétition)
        deja_fait = set(zip(df_existant['n'], df_existant['repetition']))
    else:
        deja_fait = set()

    total_configs = len(config_sizes)

    print(f"\n{'=' * 80}")
    print(f" ÉTUDE DE COMPLEXITÉ (Mode: {mode.upper()})")
    print(f"{'=' * 80}")

    for idx, (n, nb_repetitions) in enumerate(sorted(config_sizes.items()), 1):
        print(f"\n[{idx}/{total_configs}] Taille n = {n:5d}")

        for repetition in range(1, nb_repetitions + 1):
            # si on est en mode continuer, on vérifie si la ligne existe déjà
            if (n, repetition) in deja_fait:
                continue

            try:
                probleme = generer_probleme_carre(n)
                mesures = mesurer_performance(probleme)
                ligne = {
                    "n": n,
                    "repetition": repetition,
                    **mesures,
                }
                lignes.append(ligne)
            except Exception as e:
                print(f"  [ERREUR] Répétition {repetition}: {str(e)[:40]}")
                continue

            if repetition % max(1, nb_repetitions // 5) == 0:
                print(f"  Progression: {repetition}/{nb_repetitions} ({(repetition / nb_repetitions) * 100:.0f}%)")

    df = pd.DataFrame(lignes)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(FICHIER_RESULTATS, index=False)
    print(f"\n[OK] {len(df)} lignes totales sauvegardées dans {FICHIER_RESULTATS}")
    return df


def _melt_resultats(df: pd.DataFrame) -> pd.DataFrame:
    colonnes = [
        "theta_NO_s",
        "theta_BH_s",
        "t_NO_s",
        "t_BH_s",
        "theta_plus_t_NO_s",
        "theta_plus_t_BH_s",
        "theta_NO_numba_s",  # Ajout
        "theta_BH_numba_s"  # Ajout
    ]
    df_melt = df.melt(id_vars=["n", "repetition"], value_vars=colonnes, var_name="mesure", value_name="temps_s")
    return df_melt


def mesurer_performance(probleme: ProblemeTransport) -> dict:
    """Mesure thetaNO, thetaBH, tNO et tBH avec perf_counter pour la précision."""
    res = {}

    # Nord-Ouest
    p = _copier_probleme(probleme)
    start = time.perf_counter()
    p.methode_nord_ouest()
    res["theta_NO_s"] = time.perf_counter() - start

    # Balas-Hammer
    p = _copier_probleme(probleme)
    start = time.perf_counter()
    p.methode_balas_hammer()
    res["theta_BH_s"] = time.perf_counter() - start

    # Marche-Pied (NO)
    p = _copier_probleme(probleme)
    p.methode_nord_ouest()
    start = time.perf_counter()
    p.methode_marche_pied_potentiels(initialisation_deja_faite=True)
    res["t_NO_s"] = time.perf_counter() - start

    # Marche-Pied (BH)
    p = _copier_probleme(probleme)
    p.methode_balas_hammer()
    start = time.perf_counter()
    p.methode_marche_pied_potentiels(initialisation_deja_faite=True)
    res["t_BH_s"] = time.perf_counter() - start

    res["theta_plus_t_NO_s"] = res["theta_NO_s"] + res["t_NO_s"]
    res["theta_plus_t_BH_s"] = res["theta_BH_s"] + res["t_BH_s"]

    """
    Code pour comparaison complexité pyton numba
    """
    p1 = _copier_probleme(probleme)
    start = time.perf_counter()
    p1.executer_nord_ouest_fast()
    res["theta_NO_numba_s"] = time.perf_counter() - start

    # Version Numba Balas-Hammer
    p2 = _copier_probleme(probleme)
    start = time.perf_counter()
    p2.executer_balas_hammer_fast()
    res["theta_BH_numba_s"] = time.perf_counter() - start
    return res


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
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    print(f"[OK] Graphique sauvegardé: {chemin}")
    plt.show()


def tracer_moyennes(df: pd.DataFrame) -> None:
    """Trace les courbes de moyennes pour chaque mesure."""
    df_melt = _melt_resultats(df)
    mesures = list(df_melt["mesure"].unique())

    fig, axes = plt.subplots(2, 3, figsize=(18, 10), sharex=True)
    axes = axes.flatten()

    for axe, mesure in zip(axes, mesures):
        subset = df_melt[df_melt["mesure"] == mesure]

        sns.lineplot(
            data=subset,
            x="n",
            y="temps_s",
            ax=axe,
            estimator="mean",
            errorbar=None,
            marker="o",
            markersize=4
        )

        axe.set_title(f"Moyenne : {mesure}")
        axe.set_xlabel("n")
        axe.set_ylabel("Temps CPU Moyen (s)")
        axe.grid(True, alpha=0.3)

    plt.tight_layout()
    DOSSIER_SORTIE.mkdir(exist_ok=True)
    chemin = DOSSIER_SORTIE / "courbes_moyennes.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique des moyennes sauvegardé: {chemin}")
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
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
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()

    maxima.to_csv(DOSSIER_SORTIE / "maxima_temps.csv", index=False)
    return maxima


def tracer_vues_benchmark(df: pd.DataFrame) -> None:
    """Ajoute des vues synthétiques inspirées du benchmark pour le rapport."""
    df_melt = _melt_resultats(df)

    # 1) Courbes de tendance (moyenne et dispersion) par n et mesure
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
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()

    # 2) Boîtes à moustaches pour visualiser la variabilité par taille
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
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()

    # 3) Trade-off NO vs BH sur les temps complets
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
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()


def tracer_analyse_complexite(df: pd.DataFrame) -> None:
    """
    Génère 4 graphiques comparant les moyennes réelles aux complexités théoriques
    en utilisant les colonnes spécifiques : theta_NO_s, theta_BH_s, t_NO_s, t_BH_s.
    """
    df_melt = _melt_resultats(df)
    config_theorique = {
        "theta_NO_s": {"func": lambda x: x, "label": "O(n)", "titre": "Coin Nord-Ouest"},
        "theta_BH_s": {"func": lambda x: x ** 3, "label": "O(n³)", "titre": "Balas-Hammer"},
        "t_NO_s": {"func": lambda x: x ** 4, "label": "O(n³)", "titre": "Marche-Pied (depuis NO)"},
        "t_BH_s": {"func": lambda x: x ** 4, "label": "O(n³)", "titre": "Marche-Pied (depuis BH)"}
    }

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()

    for i, (colonne, info) in enumerate(config_theorique.items()):
        axe = axes[i]
        data_mesure = df_melt[df_melt["mesure"] == colonne]

        if data_mesure.empty:
            axe.set_title(f"Données absentes : {colonne}")
            print(f"[!] Colonne '{colonne}' non trouvée dans le DataFrame.")
            continue

        # calcul de la moyenne pour chaque n
        subset = data_mesure.groupby("n")["temps_s"].mean().reset_index()
        n_vals = subset["n"].values
        temps_reel = subset["temps_s"].values

        # --- TRACÉ RÉEL ---
        sns.lineplot(x=n_vals, y=temps_reel, ax=axe, label="Réel (Moyenne)",
                     marker="o", color="#1f77b4", linewidth=2.5, zorder=3)

        # --- TRACÉ THÉORIQUE ---
        y_theo_brut = np.array([info["func"](x) for x in n_vals])

        if len(y_theo_brut) > 0 and y_theo_brut[-1] > 0:
            # aligne dernier point théorique sur le dernier point réel pour comparer la forme
            echelle = temps_reel[-1] / y_theo_brut[-1]
            y_theo_scaled = y_theo_brut * echelle

            axe.plot(n_vals, y_theo_scaled, linestyle="--", color="#d62728",
                     linewidth=2, alpha=0.8, label=f"Tendance {info['label']}")

        axe.set_title(info["titre"], fontsize=14, fontweight='bold')
        axe.set_xlabel("Taille du problème (n)")
        axe.set_ylabel("Temps CPU Moyen (s)")
        axe.legend(frameon=True)
        axe.grid(True, which="both", alpha=0.3)

    plt.tight_layout()

    DOSSIER_SORTIE.mkdir(exist_ok=True, parents=True)
    chemin = DOSSIER_SORTIE / f"analyse_O_complexite_.png"

    plt.savefig(chemin, dpi=160)
    print(f"\n[OK] Graphique généré avec succès : {chemin}")
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
    plt.show()


def tracer_comparaison_efficacite(df: pd.DataFrame) -> None:
    """
    Compare directement le temps total (Initialisation + Marche-pied)
    entre Nord-Ouest et Balas-Hammer.
    """
    plt.figure(figsize=(10, 6))

    # Calcul des moyennes par n
    df_avg = df.groupby("n")[["theta_plus_t_NO_s", "theta_plus_t_BH_s"]].mean().reset_index()

    plt.plot(df_avg["n"], df_avg["theta_plus_t_NO_s"], label="Total via Nord-Ouest", marker='o')
    plt.plot(df_avg["n"], df_avg["theta_plus_t_BH_s"], label="Total via Balas-Hammer", marker='s')

    plt.title("Comparaison de l'efficacité totale : NO vs BH")
    plt.xlabel("Taille du problème (n)")
    plt.ylabel("Temps total moyen (s)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    chemin = DOSSIER_SORTIE / "comparaison_efficacite_totale.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Graphique de comparaison sauvegardé: {chemin}")
    mng = plt.get_current_fig_manager()
    mng.window.state('zoomed')
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


def tracer_comparaison_numba(df: pd.DataFrame) -> None:
    """
    Génère des graphiques comparant spécifiquement les versions Python pur et Numba.
    Utilise une échelle logarithmique pour que les deux courbes soient visibles.
    """
    df_avg = df.groupby("n")[["theta_NO_s", "theta_NO_numba_s",
                              "theta_BH_s", "theta_BH_numba_s"]].mean().reset_index()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # --- GRAPHIQUE 1 : COMPARAISON DES TEMPS (Échelle Log) ---
    ax1.plot(df_avg["n"], df_avg["theta_NO_s"], 'b-', label="Nord-Ouest (Python)")
    ax1.plot(df_avg["n"], df_avg["theta_NO_numba_s"], 'b--', label="Nord-Ouest (Numba/C)")
    ax1.plot(df_avg["n"], df_avg["theta_BH_s"], 'r-', label="Balas-Hammer (Python)")
    ax1.plot(df_avg["n"], df_avg["theta_BH_numba_s"], 'r--', label="Balas-Hammer (Numba/C)")

    ax1.set_yscale('log')
    ax1.set_title("Comparaison des temps (Échelle Logarithmique)", fontsize=12, fontweight='bold')
    ax1.set_xlabel("Taille n")
    ax1.set_ylabel("Temps (secondes)")
    ax1.legend()
    ax1.grid(True, which="both", alpha=0.3)

    # --- GRAPHIQUE 2 : FACTEUR D'ACCÉLÉRATION  ---
    speedup_no = df_avg["theta_NO_s"] / df_avg["theta_NO_numba_s"]
    speedup_bh = df_avg["theta_BH_s"] / df_avg["theta_BH_numba_s"]

    ax2.plot(df_avg["n"], speedup_no, 'b-o', label="Speedup Nord-Ouest")
    ax2.plot(df_avg["n"], speedup_bh, 'r-s', label="Speedup Balas-Hammer")
    ax2.axhline(y=1, color='black', linestyle='--', alpha=0.5)
    ax2.set_title("Facteur d'accélération (Combien de fois Numba est plus rapide)", fontsize=12, fontweight='bold')
    ax2.set_xlabel("Taille n")
    ax2.set_ylabel("Ratio (Temps Py / Temps Numba)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    chemin = DOSSIER_SORTIE / "comparaison_python_vs_numba.png"
    plt.savefig(chemin, dpi=160)
    print(f"[OK] Nouveau graphique comparatif sauvegardé : {chemin}")
    mng = plt.get_current_fig_manager()
    if hasattr(mng.window, 'state'): mng.window.state('zoomed')
    plt.show()


def main():
    """Exécute l'étude avec choix du mode et comparaison Python vs Numba."""
    import sys

    # --- ÉTAPE 0 : WARMUP NUMBA ---
    print(f"\n{'=' * 80}")
    print("[INFO] Initialisation du compilateur JIT (Numba)...")
    try:
        from structure import ProblemeTransport
        p_warmup = ProblemeTransport(2, 2)
        p_warmup.couts = [[1, 2], [3, 4]]
        p_warmup.provisions = [10, 10]
        p_warmup.commandes = [10, 10]
        p_warmup.executer_nord_ouest_fast()
        p_warmup.executer_balas_hammer_fast()
        print("[OK] Compilateur prêt. Les mesures seront précises.")
    except Exception as e:
        print(f"[!] Erreur lors du warmup Numba : {e}")
        print("[!] L'étude continuera peut-être sans les optimisations.")
    print(f"{'=' * 80}\n")

    # Choix du mode
    mode = "nouveau"
    if FICHIER_RESULTATS.exists():
        print(f"Fichier de résultats détecté : {FICHIER_RESULTATS}")
        choix = input("Voulez-vous (c)ontinuer l'étude existante ou repartir de (z)éro ? [c/z] : ").lower().strip()
        if choix == 'c':
            mode = "continuer"
        else:
            print("[!] Attention : Le fichier existant sera écrasé à la fin du processus.")

    config = CONFIG_SIZES.copy()

    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        config = {k: v for k, v in config.items() if k <= 20}
        print("[INFO] Mode RAPIDE activé (tailles réduites).")

    df = executer_etude(config_sizes=config, mode=mode)

    if df.empty:
        print("[!] Aucune donnée à traiter.")
        return

    print(f"\n{'=' * 80}")
    print(" GÉNÉRATION DES GRAPHIQUES (COMPARAISON PYTHON vs NUMBA)")
    print(f"{'=' * 80}")

    tracer_nuages(df)
    tracer_moyennes(df)
    maxima = tracer_maxima(df)
    tracer_vues_benchmark(df)
    imprimer_resume(maxima)

    # Graphiques complexité
    tracer_analyse_complexite(df)
    tracer_comparaison_efficacite(df)

    print("\n[INFO] Génération du comparatif Python vs Numba...")
    """
    Code pour comparaison complexité pyton numba
    """
    tracer_comparaison_numba(df)

    print(f"\n[OK] Étude comparative terminée avec succès !")
    print(f"Les résultats sont disponibles dans : {DOSSIER_SORTIE}")


if __name__ == "__main__":
    main()
