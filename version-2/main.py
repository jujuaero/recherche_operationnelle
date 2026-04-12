import pandas as pd
import matplotlib.pyplot as plt

try:
    df = pd.read_csv('complexite_stats.csv')
except FileNotFoundError:
    print("Erreur : Le fichier 'complexite_stats.csv' est introuvable.")
    exit()

df['totalNO'] = df['thetaNO'] + df['tNO']
df['totalBH'] = df['thetaBH'] + df['tBH']
df_mean = df.groupby('n').mean().reset_index()

plots = [
    ('thetaNO', 'Temps Nord-Ouest (θNO)'),
    ('thetaBH', 'Temps Balas-Hammer (θBH)'),
    ('tNO', 'Temps Marche-pied via NO (tNO)'),
    ('tBH', 'Temps Marche-pied via BH (tBH)'),
    ('totalNO', 'Total (θNO + tNO)'),
    ('totalBH', 'Total (θBH + tBH)')
]

# Nuages de points (sans notation scientifique)
plt.figure(figsize=(15, 10))
plt.subplots_adjust(hspace=0.4, wspace=0.3)
for i, (col, title) in enumerate(plots, 1):
    plt.subplot(3, 2, i)
    plt.scatter(df['n'], df[col], alpha=0.5, s=10, c='blue')
    plt.title(title)
    plt.xlabel('Taille du problème (n)')
    plt.ylabel('Temps (secondes)')
    plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('nuages_points_complexite_decimal.png', dpi=300)
print("Graphiques (nuages de points) sauvegardés sous 'nuages_points_complexite_decimal.png'")

# Courbes avec points reliés
plt.figure(figsize=(15, 10))
plt.subplots_adjust(hspace=0.4, wspace=0.3)
for i, (col, title) in enumerate(plots, 1):
    plt.subplot(3, 2, i)
    plt.plot(df_mean['n'], df_mean[col], marker='o', linestyle='-', markersize=4, linewidth=1)
    plt.title(f"{title} (courbe)")
    plt.xlabel('Taille du problème (n)')
    plt.ylabel('Temps (secondes)')
    plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('courbes_points_complexite.png', dpi=300)
print("Graphiques (courbes) sauvegardés sous 'courbes_points_complexite.png'")

# Comparatif des différentes complexités sur le même graphique
plt.figure(figsize=(12, 8))
for col, title in plots:
    plt.plot(df_mean['n'], df_mean[col], marker='o', markersize=4, linewidth=1, label=title)
plt.title("Comparatif des complexités")
plt.xlabel('Taille du problème (n)')
plt.ylabel('Temps (secondes)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('comparatif_complexite.png', dpi=300)
print("Graphique comparatif sauvegardé sous 'comparatif_complexite.png'")

# Graphique logarithmique
plt.figure(figsize=(12, 8))
for col, title in plots:
    plt.plot(df_mean['n'], df_mean[col], marker='o', markersize=4, linewidth=1, label=title)
plt.yscale('log')
plt.title("Comparatif des complexités (échelle log)")
plt.xlabel('Taille du problème (n)')
plt.ylabel('Temps (secondes)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('comparatif_complexite_log.png', dpi=300)


# Graphique pour les petites valeurs
plt.figure(figsize=(12, 8))
for col, title in [('thetaNO', 'θNO'), ('thetaBH', 'θBH'), ('tBH', 'tBH')]:
    plt.plot(df_mean['n'], df_mean[col], marker='o', markersize=4, linewidth=1, label=title)
plt.title("Comparatif des petites complexités")
plt.xlabel('Taille du problème (n)')
plt.ylabel('Temps (secondes)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('comparatif_petites_complexites.png', dpi=300)

# Graphique pour les grandes valeurs
plt.figure(figsize=(12, 8))
for col, title in [('tNO', 'tNO'), ('totalNO', 'Total NO'), ('totalBH', 'Total BH')]:
    plt.plot(df_mean['n'], df_mean[col], marker='o', markersize=4, linewidth=1, label=title)
plt.title("Comparatif des grandes complexités")
plt.xlabel('Taille du problème (n)')
plt.ylabel('Temps (secondes)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig('comparatif_grandes_complexites.png', dpi=300)

plt.show()
