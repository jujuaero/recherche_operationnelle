import random
import os


def generer_fichier_transport(n, m, nom_fichier=None):
    """
    Génère un fichier de transport équilibré de taille n x m.
    """
    if nom_fichier is None:
        nom_fichier = f"transport_test_{n}x{m}.txt"

    # 1. Générer des coûts unitaires aléatoires (ex: entre 1 et 100)
    couts = [[random.randint(1, 100) for _ in range(m)] for _ in range(n)]

    # 2. Générer des provisions et commandes équilibrées
    # On génère des valeurs aléatoires, puis on ajuste la dernière pour équilibrer
    provisions = [random.randint(10, 500) for _ in range(n)]
    total_provisions = sum(provisions)

    # Répartir le total dans les commandes
    commandes = []
    reste = total_provisions
    for i in range(m - 1):
        # On prend une part aléatoire du reste (au moins 1)
        val = random.randint(1, max(1, reste // (m - i)))
        commandes.append(val)
        reste -= val
    commandes.append(reste)  # Le dernier client prend tout le reste

    # 3. Écriture du fichier
    # Créer le dossier 'donnees' s'il n'existe pas pour correspondre à ton structure.py
    if not os.path.exists("donnees"):
        os.makedirs("donnees")

    chemin_complet = os.path.join("donnees", nom_fichier)

    with open(chemin_complet, 'w', encoding='utf-8') as f:
        # Ligne 1 : n m
        f.write(f"{n} {m}\n")

        # Lignes 2 à n+1 : couts... provision
        for i in range(n):
            ligne_couts = " ".join(map(str, couts[i]))
            f.write(f"{ligne_couts} {provisions[i]}\n")

        # Ligne n+2 : commandes
        ligne_commandes = " ".join(map(str, commandes))
        f.write(f"{ligne_commandes}\n")

    print(f"✓ Fichier '{chemin_complet}' généré avec succès ({n} fournisseurs, {m} clients).")


if __name__ == "__main__":
    print("--- Générateur de Problèmes de Transport ---")
    try:
        n_input = int(input("Nombre de fournisseurs (n) : "))
        m_input = int(input("Nombre de clients (m) : "))
        num_fichier = input("Numéro ou nom pour le fichier (ex: 99) : ")

        nom = f"transport{num_fichier}.txt"
        generer_fichier_transport(n_input, m_input, nom)

    except ValueError:
        print("Erreur : Veuillez entrer des nombres entiers valides.")