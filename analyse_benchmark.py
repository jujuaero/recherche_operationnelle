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
        print(f"✓ {len(self.df)} résultats chargés")
    
    def resume_statistiques(self):
        """Affiche un résumé des statistiques principales"""
        print("\n" + "="*80)
        print("RÉSUMÉ STATISTIQUE GLOBAL")
        print("="*80 + "\n")
        
        # Groupé par algorithme
        print("PAR ALGORITHME:\n")
        for algo in self.df['algorithme'].unique():
            subset = self.df[self.df['algorithme'] == algo]
            print(f"  {algo}:")
            print(f"    • Temps moyen:     {subset['temps_ms'].mean():.4f} ms")
            print(f"    • Temps médian:    {subset['temps_ms'].median():.4f} ms")
            print(f"    • Temps max:       {subset['temps_ms'].max():.4f} ms")
            print(f"    • Écart-type:      {subset['temps_ms'].std():.4f} ms")
            print(f"    • Validité:        {100*subset['validations_ok'].mean():.1f}%")
            print()
    
    def complexite_par_dimension(self):
        """Analyse la complexité en fonction de n et m"""
        print("\n" + "="*80)
        print("ANALYSE DE COMPLEXITÉ")
        print("="*80 + "\n")
        
        for algo in sorted(self.df['algorithme'].unique()):
            print(f"\n{algo.upper()}:")
            subset = self.df[self.df['algorithme'] == algo]
            
            # Grouper par taille
            grouped = subset.groupby(['n', 'm'])['temps_ms'].agg(['mean', 'std', 'count'])
            
            print(" " * 10 + "n × m) | Temps (ms) | Écart-type | Tests")
            print("-" * 60)
            
            for (n, m), row in grouped.iterrows():
                nb = int(row['count'])
                print(f"  {n:2d} × {m:2d} | {row['mean']:10.4f} | {row['std']:10.4f} | {nb:4d}")
            
            # Estimer l'ordre de complexité
            print(f"\n  → Tendance (augmentation temps par doublement de taille) :")
            sizes = sorted(grouped.index.unique())
            for i in range(len(sizes) - 1):
                n1, m1 = sizes[i]
                n2, m2 = sizes[i + 1]
                t1 = grouped.loc[(n1, m1), 'mean']
                t2 = grouped.loc[(n2, m2), 'mean']
                factor = (n2 * m2) / (n1 * m1)
                ratio = t2 / t1
                print(f"    {n1}×{m1} → {n2}×{m2}: {ratio:.2f}x (facteur taille: {factor:.1f}x)")
    
    def comparaison_algos(self):
        """Compare les algorithmes entre eux"""
        print("\n" + "="*80)
        print("COMPARAISON ENTRE ALGORITHMES")
        print("="*80 + "\n")
        
        for (n, m), group in self.df.groupby(['n', 'm']):
            print(f"\nConfiguration {n} × {m}:")
            
            # Temps
            print("  Temps (ms):")
            for algo in sorted(group['algorithme'].unique()):
                temps = group[group['algorithme'] == algo]['temps_ms'].mean()
                print(f"    • {algo:20s}: {temps:.4f} ms")
            
            # Rapport au plus rapide
            fastest = group.groupby('algorithme')['temps_ms'].mean().min()
            print("  \n  Ratio par rapport au plus rapide:")
            for algo in sorted(group['algorithme'].unique()):
                times = group[group['algorithme'] == algo]['temps_ms'].mean()
                ratio = times / fastest
                print(f"    • {algo:20s}: {ratio:.2f}x")
            
            # Qualité (coût)
            print("\n  Coût moyen:")
            for algo in sorted(group['algorithme'].unique()):
                cout = group[group['algorithme'] == algo]['cout_total'].mean()
                print(f"    • {algo:20s}: {cout:.0f}")
    
    def plot_temps_vs_dimension(self):
        """Plot temps en fonction de la dimension"""
        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        
        # Plot 1 : Temps selon n (fixe m)
        sns.lineplot(data=self.df, x='n', y='temps_ms', hue='algorithme', 
                     marker='o', ax=axes[0])
        axes[0].set_title('Temps vs Nombre de Fournisseurs (n)')
        axes[0].set_ylabel('Temps (ms)')
        
        # Plot 2 : Temps selon m (fixe n)
        sns.lineplot(data=self.df, x='m', y='temps_ms', hue='algorithme', 
                     marker='o', ax=axes[1])
        axes[1].set_title('Temps vs Nombre de Clients (m)')
        axes[1].set_ylabel('Temps (ms)')
        
        # Plot 3 : Temps selon n*m (produit)
        self.df['n_times_m'] = self.df['n'] * self.df['m']
        sns.lineplot(data=self.df, x='n_times_m', y='temps_ms', hue='algorithme', 
                     marker='o', ax=axes[2])
        axes[2].set_title('Temps vs Taille (n × m)')
        axes[2].set_ylabel('Temps (ms)')
        axes[2].set_xlabel('Taille (n × m)')
        
        plt.tight_layout()
        plt.savefig('benchmark_temps.png', dpi=150)
        print("\n✓ Graphique sauvegardé: benchmark_temps.png")
        plt.show()
    
    def plot_boite_temps(self):
        """Diagramme en boîte du temps par algorithme et configuration"""
        g = sns.FacetGrid(self.df, col='algorithme', height=4, aspect=1)
        g.map(sns.boxplot, 'n', 'temps_ms', hue='m', dodge=True)
        g.set_titles("{col_name}")
        
        plt.tight_layout()
        plt.savefig('benchmark_boites.png', dpi=150)
        print("✓ Graphique sauvegardé: benchmark_boites.png")
        plt.show()
    
    def plot_cout_vs_temps(self):
        """Scatter plot coût vs temps pour voir le trade-off"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Par ordre de taille
        size_levels = sorted(self.df[['n', 'm']].drop_duplicates().apply(lambda x: x['n']*x['m'], axis=1).unique())
        colors = {algo: color for algo, color in zip(
            sorted(self.df['algorithme'].unique()),
            plt.cm.Set2(np.linspace(0, 1, len(self.df['algorithme'].unique())))
        )}
        
        for algo in self.df['algorithme'].unique():
            subset = self.df[self.df['algorithme'] == algo]
            axes[0].scatter(subset['temps_ms'], subset['cout_total'], 
                           label=algo, alpha=0.6, s=30, color=colors[algo])
        
        axes[0].set_xlabel('Temps (ms)')
        axes[0].set_ylabel('Coût total')
        axes[0].set_title('Trade-off Temps vs Coût')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Distribution des temps
        for algo in self.df['algorithme'].unique():
            subset = self.df[self.df['algorithme'] == algo]
            axes[1].hist(subset['temps_ms'], alpha=0.5, label=algo, bins=30)
        
        axes[1].set_xlabel('Temps (ms)')
        axes[1].set_ylabel('Fréquence')
        axes[1].set_title('Distribution des Temps')
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig('benchmark_cout_vs_temps.png', dpi=150)
        print("✓ Graphique sauvegardé: benchmark_cout_vs_temps.png")
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
        print(f"\n✓ Synthèse exportée: {fichier_synthese}")
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
        print(f"⚠️ Erreur lors de la génération de graphiques: {e}")
        print("  Installez matplotlib et seaborn: pip install matplotlib seaborn")
    
    print("\n✓ Analyse terminée !")


if __name__ == "__main__":
    main()
