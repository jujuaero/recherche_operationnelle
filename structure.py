"""
Structure de données pour le problème de transport.
Gère la matrice des coûts, les provisions, les commandes et la matrice de transport.
"""

import os
from copy import deepcopy


class ProblemeTransport:
    """
    Structure représentant un problème de transport équilibré.
    
    Attributs:
        n: nombre de fournisseurs
        m: nombre de clients
        couts: matrice n x m des coûts unitaires
        provisions: vecteur n des provisions des fournisseurs
        commandes: vecteur m des demandes des clients
        transport: matrice n x m de la solution (quantités transportées)
        base: ensemble des indices (i,j) formant la base pour la méthode des potentiels
    """
    
    def __init__(self, n=0, m=0):
        self.n = n  # nombre de fournisseurs
        self.m = m  # nombre de clients
        self.couts = []  # matrice n x m
        self.provisions = []  # vecteur n
        self.commandes = []  # vecteur m
        self.transport = []  # matrice n x m (solution)
        self.base = set()  # cellules de la base
    
    @staticmethod
    def charger_depuis_fichier(nom_fichier):
        """
        Charge un problème de transport depuis un fichier .txt
        
        Format:
            Ligne 1: n m
            Lignes 2 à n+1: a_1,1 a_1,2 ... a_1,m P_1
                            ...
                            a_n,1 a_n,2 ... a_n,m P_n
            Ligne n+2: C_1 C_2 ... C_m
        
        Les prix unitaires sont en bleu, provisions en dernière colonne.
        """
        probleme = ProblemeTransport()
        
        # Déterminer le chemin du fichier
        if not os.path.exists(nom_fichier):
            chemin_fichier = os.path.join("donnees", nom_fichier)
        else:
            chemin_fichier = nom_fichier
        
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            lignes = [ligne.strip() for ligne in f.readlines() if ligne.strip()]
        
        # Lecture n et m
        n, m = map(int, lignes[0].split())
        probleme.n = n
        probleme.m = m
        
        # Lecture coûts et provisions
        probleme.couts = []
        probleme.provisions = []
        
        for i in range(1, n + 1):
            elements = list(map(int, lignes[i].split()))
            ligne_couts = elements[:m]
            provision = elements[m]
            
            probleme.couts.append(ligne_couts)
            probleme.provisions.append(provision)
        
        # Lecture commandes
        commandes = list(map(int, lignes[n + 1].split()))
        probleme.commandes = commandes
        
        # Vérifier l'équilibrage
        if sum(probleme.provisions) != sum(probleme.commandes):
            raise ValueError(
                f"Problème non équilibré: sum(provisions)={sum(probleme.provisions)}, "
                f"sum(commandes)={sum(probleme.commandes)}"
            )
        
        # Initialiser matrice de transport vide
        probleme.transport = [[0] * m for _ in range(n)]
        
        return probleme
    
    def afficher_matrice_couts(self):
        """Affiche la matrice des coûts avec provisions"""
        return self._afficher_matrice(
            self.couts,
            titre="MATRICE DES COÛTS",
            extras_colonne=self.provisions,
            label_extra="Provisions"
        )
    
    def afficher_matrice_transport(self):
        """Affiche la matrice de transport avec provisions"""
        return self._afficher_matrice(
            self.transport,
            titre="MATRICE DE TRANSPORT",
            extras_colonne=self.provisions,
            label_extra="Provisions"
        )
    
    def afficher_table_potentiels(self, potentiels_u, potentiels_v):
        """Affiche les potentiels u(i) et v(j)"""
        resultat = f"\nTABLE DES POTENTIELS\n"
        resultat += "=" * 80 + "\n"
        resultat += f"u(i) = potentiels des fournisseurs\n"
        resultat += f"v(j) = potentiels des clients\n\n"
        
        # Afficher u(i)
        resultat += f"{'Fournisseur':<20} | {'u(i)':<10}\n"
        resultat += "-" * 35 + "\n"
        for i in range(self.n):
            val = potentiels_u[i] if potentiels_u[i] is not None else "?"
            resultat += f"{'Fournisseur ' + str(i):<20} | {str(val):<10}\n"
        
        resultat += "\n"
        
        # Afficher v(j)
        resultat += f"{'Client':<20} | {'v(j)':<10}\n"
        resultat += "-" * 35 + "\n"
        for j in range(self.m):
            val = potentiels_v[j] if potentiels_v[j] is not None else "?"
            resultat += f"{'Client ' + str(j):<20} | {str(val):<10}\n"
        
        resultat += "=" * 80
        return resultat
    
    def afficher_table_marginaux(self, marginaux):
        """Affiche la table des coûts marginaux"""
        resultat = f"\nTABLE DES COÛTS MARGINAUX (pour cellules hors base)\n"
        resultat += "=" * 80 + "\n"
        
        largeur = 8
        
        # En-tête
        entete = f"{'F/C':<5} |"
        for j in range(self.m):
            entete += f"{f'C{j}':<{largeur}}"
        resultat += entete + "\n"
        resultat += "-" * len(entete) + "\n"
        
        # Lignes
        for i in range(self.n):
            ligne = f"{'F' + str(i):<5} |"
            for j in range(self.m):
                if (i, j) in self.base:
                    val = "BASE"
                elif (i, j) in marginaux:
                    val = str(marginaux[(i, j)])
                else:
                    val = "-"
                ligne += f"{val:<{largeur}}"
            resultat += ligne + "\n"
        
        resultat += "=" * 80
        return resultat
    
    def cout_total(self):
        """Calcule le coût total actuel du transport"""
        cout = 0
        for i in range(self.n):
            for j in range(self.m):
                cout += self.couts[i][j] * self.transport[i][j]
        return cout
    
    def _afficher_matrice(self, matrice, titre="", extras_colonne=None, label_extra=""):
        """
        Affiche une matrice de manière formatée et lisible.
        
        Args:
            matrice: matrice à afficher
            titre: titre
            extras_colonne: colonne supplémentaire à ajouter (ex: provisions)
            label_extra: label de la colonne supplémentaire
        """
        resultat = f"\n{titre}\n"
        resultat += "=" * 100 + "\n"
        
        # Calculer largeur
        largeur_max = 4
        if extras_colonne:
            for val in extras_colonne:
                largeur_max = max(largeur_max, len(str(val)))
        for i in range(len(matrice)):
            for j in range(len(matrice[0])):
                largeur_max = max(largeur_max, len(str(matrice[i][j])))
        
        largeur = largeur_max + 2
        
        # En-tête colonnes
        entete = f"{'F/C':<10} |"
        for j in range(self.m):
            entete += f"{f'C{j}':<{largeur}}"
        if extras_colonne:
            entete += f"{label_extra:<{largeur}}"
        
        resultat += entete + "\n"
        resultat += "-" * len(entete) + "\n"
        
        # Lignes matrice
        for i in range(len(matrice)):
            ligne = f"{'F' + str(i):<10} |"
            for j in range(len(matrice[0])):
                ligne += f"{str(matrice[i][j]):<{largeur}}"
            if extras_colonne:
                ligne += f"{str(extras_colonne[i]):<{largeur}}"
            resultat += ligne + "\n"
        
        # Ligne commandes si applicable
        if self.commandes:
            ligne = f"{'Commandes':<10} |"
            for j in range(self.m):
                ligne += f"{str(self.commandes[j]):<{largeur}}"
            resultat += ligne + "\n"
        
        resultat += "=" * 100
        return resultat
