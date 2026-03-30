"""
Analyse post-benchmark des résultats avec visualisations.
À utiliser après avoir exécuté benchmark.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class AnalyseBenchmark:
    """Analyse détaillée des résultats de benchmark"""
    
    def __init__(self, fichier_csv="resultats_benchmark.csv"):
        self.fichier_csv = fichier_csv
        if not Path(fichier_csv).exists():
            raise FileNotFoundError(f"Fichier '{fichier_csv}' non trouvé")
        
        self.df = pd.read_csv(fichier_csv)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        # Etiquette d'affichage pour distinguer marche_pied selon l'initialisation
        self.df['algo_affichage'] = self.df.apply(
            lambda row: f"marche_pied ({row['initialisation']})"
            if row['algorithme'] == 'marche_pied' and pd.notna(row['initialisation'])
            else row['algorithme'],
            axis=1
        )
        print(f"[OK] {len(self.df)} resultats charges")
    
    def resume_statistiques(self):
        """Affiche un résumé des statistiques principales"""
        print("\n" + "="*80)
        print("RÉSUMÉ STATISTIQUE GLOBAL")
        print("="*80 + "\n")
        
        # Groupé par algorithme + initialisation
        print("PAR ALGORITHME:\n")
        
        # Algorithmes simples
        for algo in ['nord_ouest', 'balas_hammer']:
            if algo in self.df['algorithme'].values:
                subset = self.df[self.df['algorithme'] == algo]
                print(f"  {algo}:")
                print(f"    - Temps moyen:     {subset['temps_ms'].mean():.4f} ms")
                print(f"    - Temps median:    {subset['temps_ms'].median():.4f} ms")
                print(f"    - Temps max:       {subset['temps_ms'].max():.4f} ms")
                print(f"    - Ecart-type:      {subset['temps_ms'].std():.4f} ms")
                print(f"    - Validite:        {100*subset['validations_ok'].mean():.1f}%")
                print()
        
        # Marche pied avec initialisations
        if 'marche_pied' in self.df['algorithme'].values:
            for init in ['nord_ouest', 'balas_hammer']:
                subset = self.df[(self.df['algorithme'] == 'marche_pied') & 
                                (self.df['initialisation'] == init)]
                if len(subset) > 0:
                    print(f"  marche_pied (init: {init}):")
                    print(f"    - Temps moyen:     {subset['temps_ms'].mean():.4f} ms")
                    print(f"    - Temps median:    {subset['temps_ms'].median():.4f} ms")
                    print(f"    - Temps max:       {subset['temps_ms'].max():.4f} ms")
                    print(f"    - Ecart-type:      {subset['temps_ms'].std():.4f} ms")
                    print(f"    - Validite:        {100*subset['validations_ok'].mean():.1f}%")
                    print()
    
    def complexite_par_dimension(self):
        """Analyse la complexité en fonction de n et m"""
        print("\n" + "="*80)
        print("ANALYSE DE COMPLEXITE")
        print("="*80 + "\n")
        
        algos_simples = ['nord_ouest', 'balas_hammer']
        
        for algo in algos_simples:
            if algo in self.df['algorithme'].values:
                print(f"\n{algo.upper()}:")
                subset = self.df[self.df['algorithme'] == algo]
                
                # Grouper par taille
                grouped = subset.groupby(['n', 'm'])['temps_ms'].agg(['mean', 'std', 'count'])
                
                print(" " * 10 + "n x m) | Temps (ms) | Ecart-type | Tests")
                print("-" * 60)
                
                for (n, m), row in grouped.iterrows():
                    nb = int(row['count'])
                    print(f"  {n:2d} x {m:2d} | {row['mean']:10.4f} | {row['std']:10.4f} | {nb:4d}")
                
                # Estimer l'ordre de complexité
                print(f"\n  => Tendance (augmentation temps par doublement de taille) :")
                sizes = sorted(grouped.index.unique())
                for i in range(len(sizes) - 1):
                    n1, m1 = sizes[i]
                    n2, m2 = sizes[i + 1]
                    t1 = grouped.loc[(n1, m1), 'mean']
                    t2 = grouped.loc[(n2, m2), 'mean']
                    factor = (n2 * m2) / (n1 * m1)
                    ratio = t2 / t1
                    print(f"    {n1}x{m1} => {n2}x{m2}: {ratio:.2f}x (facteur taille: {factor:.1f}x)")
        
        # Marche pied avec initialisations
        if 'marche_pied' in self.df['algorithme'].values:
            for init in ['nord_ouest', 'balas_hammer']:
                subset = self.df[(self.df['algorithme'] == 'marche_pied') & 
                                (self.df['initialisation'] == init)]
                if len(subset) > 0:
                    print(f"\nMARCHE_PIED (init: {init}):")
                    
                    # Grouper par taille
                    grouped = subset.groupby(['n', 'm'])['temps_ms'].agg(['mean', 'std', 'count'])
                    
                    print(" " * 10 + "n x m) | Temps (ms) | Ecart-type | Tests")
                    print("-" * 60)
                    
                    for (n, m), row in grouped.iterrows():
                        nb = int(row['count'])
                        print(f"  {n:2d} x {m:2d} | {row['mean']:10.4f} | {row['std']:10.4f} | {nb:4d}")
                    
                    # Estimer l'ordre de complexité
                    print(f"\n  => Tendance (augmentation temps par doublement de taille) :")
                    sizes = sorted(grouped.index.unique())
                    for i in range(len(sizes) - 1):
                        n1, m1 = sizes[i]
                        n2, m2 = sizes[i + 1]
                        t1 = grouped.loc[(n1, m1), 'mean']
                        t2 = grouped.loc[(n2, m2), 'mean']
                        factor = (n2 * m2) / (n1 * m1)
                        ratio = t2 / t1
                        print(f"    {n1}x{m1} => {n2}x{m2}: {ratio:.2f}x (facteur taille: {factor:.1f}x)")
    
    def comparaison_algos(self):
        """Compare les algorithmes entre eux"""
        print("\n" + "="*80)
        print("COMPARAISON ENTRE ALGORITHMES")
        print("="*80 + "\n")
        
        for (n, m), group in self.df.groupby(['n', 'm']):
            print(f"\nConfiguration {n} x {m}:")
            
            # Temps pour algos simples
            print("  Temps (ms):")
            for algo in ['nord_ouest', 'balas_hammer']:
                subset = group[group['algorithme'] == algo]
                if len(subset) > 0:
                    temps = subset['temps_ms'].mean()
                    print(f"    - {algo:20s}: {temps:.4f} ms")
            
            # Temps pour marche pied avec différentes initialisations
            if 'marche_pied' in group['algorithme'].values:
                for init in ['nord_ouest', 'balas_hammer']:
                    subset = group[(group['algorithme'] == 'marche_pied') & 
                                   (group['initialisation'] == init)]
                    if len(subset) > 0:
                        temps = subset['temps_ms'].mean()
                        print(f"    - marche_pied({init:4s}): {temps:.4f} ms")
            
            # Rapport au plus rapide
            fastest = group['temps_ms'].min()
            print("\n  Ratio par rapport au plus rapide:")
            for algo in ['nord_ouest', 'balas_hammer']:
                subset = group[group['algorithme'] == algo]
                if len(subset) > 0:
                    times = subset['temps_ms'].mean()
                    ratio = times / fastest
                    print(f"    - {algo:20s}: {ratio:.2f}x")
            
            # Ratio pour marche pied
            if 'marche_pied' in group['algorithme'].values:
                for init in ['nord_ouest', 'balas_hammer']:
                    subset = group[(group['algorithme'] == 'marche_pied') & 
                                   (group['initialisation'] == init)]
                    if len(subset) > 0:
                        times = subset['temps_ms'].mean()
                        ratio = times / fastest
                        print(f"    - marche_pied({init:4s}): {ratio:.2f}x")
            
            # Qualité (coût)
            print("\n  Cout moyen:")
            for algo in ['nord_ouest', 'balas_hammer']:
                subset = group[group['algorithme'] == algo]
                if len(subset) > 0:
                    cout = subset['cout_total'].mean()
                    print(f"    - {algo:20s}: {cout:.0f}")
            
            # Cout pour marche pied
            if 'marche_pied' in group['algorithme'].values:
                for init in ['nord_ouest', 'balas_hammer']:
                    subset = group[(group['algorithme'] == 'marche_pied') & 
                                   (group['initialisation'] == init)]
                    if len(subset) > 0:
                        cout = subset['cout_total'].mean()
                        print(f"    - marche_pied({init:4s}): {cout:.0f}")
    
    def plot_temps_vs_dimension(self):
        """Plot temps en fonction de la dimension"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        # Plot 1 : Temps selon n (fixe m)
        sns.lineplot(data=self.df, x='n', y='temps_ms', hue='algo_affichage', 
                     marker='o', ax=axes[0])
        axes[0].set_title('Temps vs Nombre de Fournisseurs (n)')
        axes[0].set_ylabel('Temps (ms)')
        
        # Plot 2 : Temps selon m (fixe n)
        sns.lineplot(data=self.df, x='m', y='temps_ms', hue='algo_affichage', 
                     marker='o', ax=axes[1])
        axes[1].set_title('Temps vs Nombre de Clients (m)')
        axes[1].set_ylabel('Temps (ms)')
        
        # Plot 3 : Temps selon n*m (produit)
        self.df['n_times_m'] = self.df['n'] * self.df['m']
        sns.lineplot(data=self.df, x='n_times_m', y='temps_ms', hue='algo_affichage', 
                     marker='o', ax=axes[2])
        axes[2].set_title('Temps vs Taille (n × m)')
        axes[2].set_ylabel('Temps (ms)')
        axes[2].set_xlabel('Taille (n × m)')
        
        plt.tight_layout()
        plt.savefig('benchmark_temps.png', dpi=150)
        print("\n[OK] Graphique sauvegarde: benchmark_temps.png")
        plt.show()
    
    def plot_boite_temps(self):
        """Diagramme en boîte du temps par algorithme et configuration"""
        g = sns.FacetGrid(self.df, col='algo_affichage', height=4, aspect=1)
        g.map_dataframe(sns.boxplot, x='n', y='temps_ms', hue='m', dodge=True)
        g.set_titles("{col_name}")
        g.add_legend()
        
        plt.tight_layout()
        plt.savefig('benchmark_boites.png', dpi=150)
        print("[OK] Graphique sauvegarde: benchmark_boites.png")
        plt.show()
    
    def plot_cout_vs_temps(self):
        """Scatter plot coût vs temps pour voir le trade-off"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Par ordre de taille
        size_levels = sorted(self.df[['n', 'm']].drop_duplicates().apply(lambda x: x['n']*x['m'], axis=1).unique())
        colors = {algo: color for algo, color in zip(
            sorted(self.df['algo_affichage'].unique()),
            plt.cm.Set2(np.linspace(0, 1, len(self.df['algo_affichage'].unique())))
        )}
        
        for algo in self.df['algo_affichage'].unique():
            subset = self.df[self.df['algo_affichage'] == algo]
            axes[0].scatter(subset['temps_ms'], subset['cout_total'], 
                           label=algo, alpha=0.6, s=30, color=colors[algo])
        
        axes[0].set_xlabel('Temps (ms)')
        axes[0].set_ylabel('Coût total')
        axes[0].set_title('Trade-off Temps vs Coût')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Distribution des temps
        for algo in self.df['algo_affichage'].unique():
            subset = self.df[self.df['algo_affichage'] == algo]
            axes[1].hist(subset['temps_ms'], alpha=0.5, label=algo, bins=30)
        
        axes[1].set_xlabel('Temps (ms)')
        axes[1].set_ylabel('Fréquence')
        axes[1].set_title('Distribution des Temps')
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig('benchmark_cout_vs_temps.png', dpi=150)
        print("[OK] Graphique sauvegarde: benchmark_cout_vs_temps.png")
        plt.show()
    
    def exporter_synthese(self, fichier_synthese="synthese.csv"):
        """Exporte une synthèse pour utilisation ultérieure"""
        # Agrégation par (n, m, algorithme)
        synthese = self.df.groupby(['n', 'm', 'algorithme']).agg({
            'temps_ms': ['mean', 'std', 'min', 'max', 'count'],
            'cout_total': ['mean', 'std', 'min', 'max'],
            'validations_ok': 'mean'
        }).round(4)
        
        synthese.to_csv(fichier_synthese)
        print(f"\n[OK] Synthese exportee: {fichier_synthese}")
        return synthese


def main():
    """Exécute l'analyse complète"""
    print("\nCHARGEMENT DES RÉSULTATS...")
    
    analyse = AnalyseBenchmark("resultats_benchmark.csv")
    
    # Exécuter tous les analyses
    analyse.resume_statistiques()
    analyse.complexite_par_dimension()
    analyse.comparaison_algos()
    analyse.exporter_synthese()
    
    # Générer les graphiques
    print("\n" + "="*80)
    print("GÉNÉRATION DES VISUALISATIONS")
    print("="*80)
    
    try:
        analyse.plot_temps_vs_dimension()
        analyse.plot_boite_temps()
        analyse.plot_cout_vs_temps()
    except Exception as e:
        print(f"[WARNING] Erreur lors de la generation de graphiques: {e}")
        print("  Installez matplotlib et seaborn: pip install matplotlib seaborn")
    
    print("\n[OK] Analyse terminee !")


if __name__ == "__main__":
    main()
