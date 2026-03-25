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

    def methode_nord_ouest(self):
        """
        Construit une solution initiale par la méthode du coin Nord-Ouest.

        Returns:
            str: résumé textuel des allocations effectuées.
        """
        if self.n == 0 or self.m == 0:
            raise ValueError("Problème vide: dimensions invalides.")

        # Réinitialiser la solution et la base
        self.transport = [[0] * self.m for _ in range(self.n)]
        self.base = set()

        provisions_restantes = self.provisions.copy()
        commandes_restantes = self.commandes.copy()

        i, j = 0, 0
        etapes = []

        while i < self.n and j < self.m:
            quantite = min(provisions_restantes[i], commandes_restantes[j])
            self.transport[i][j] = quantite
            self.base.add((i, j))
            etapes.append(
                f"Affecter {quantite} à (F{i}, C{j}) | "
                f"Reste F{i}={provisions_restantes[i] - quantite}, "
                f"Reste C{j}={commandes_restantes[j] - quantite}"
            )

            provisions_restantes[i] -= quantite
            commandes_restantes[j] -= quantite

            # Si la ligne et la colonne se ferment en même temps, avancer en diagonale.
            # On ajoute une cellule dégénérée (0) dans la base pour garder n+m-1 cellules.
            if provisions_restantes[i] == 0 and commandes_restantes[j] == 0:
                if i + 1 < self.n:
                    self.base.add((i + 1, j))
                elif j + 1 < self.m:
                    self.base.add((i, j + 1))
                i += 1
                j += 1
            elif provisions_restantes[i] == 0:
                i += 1
            else:
                j += 1

        if len(self.base) > self.n + self.m - 1:
            # Sécurité: ne pas dépasser la taille de base attendue.
            base_ordonnee = sorted(self.base)
            self.base = set(base_ordonnee[: self.n + self.m - 1])

        resultat = "\nMÉTHODE DU COIN NORD-OUEST\n"
        resultat += "=" * 80 + "\n"
        for k, etape in enumerate(etapes, 1):
            resultat += f"{k:>2}. {etape}\n"
        resultat += "=" * 80 + "\n"
        resultat += f"Coût total obtenu: {self.cout_total()}\n"
        resultat += f"Taille de base: {len(self.base)} (attendu: {self.n + self.m - 1})"

        return resultat

    def methode_balas_hammer(self):
        """
        Construit une solution initiale avec la méthode de Balas-Hammer
        (aussi connue comme approximation de Vogel).

        Returns:
            str: résumé textuel des étapes et du coût obtenu.
        """
        if self.n == 0 or self.m == 0:
            raise ValueError("Problème vide: dimensions invalides.")

        self.transport = [[0] * self.m for _ in range(self.n)]
        self.base = set()

        provisions_restantes = self.provisions.copy()
        commandes_restantes = self.commandes.copy()

        lignes_actives = set(range(self.n))
        colonnes_actives = set(range(self.m))
        etapes = []

        def penalite_ligne(i):
            couts_actifs = sorted(self.couts[i][j] for j in colonnes_actives)
            if len(couts_actifs) == 0:
                return -1
            if len(couts_actifs) == 1:
                return couts_actifs[0]
            return couts_actifs[1] - couts_actifs[0]

        def penalite_colonne(j):
            couts_actifs = sorted(self.couts[i][j] for i in lignes_actives)
            if len(couts_actifs) == 0:
                return -1
            if len(couts_actifs) == 1:
                return couts_actifs[0]
            return couts_actifs[1] - couts_actifs[0]

        def meilleure_colonne_de_ligne(i):
            return min(colonnes_actives, key=lambda j: self.couts[i][j])

        def meilleure_ligne_de_colonne(j):
            return min(lignes_actives, key=lambda i: self.couts[i][j])

        while lignes_actives and colonnes_actives:
            candidats = []

            for i in lignes_actives:
                p = penalite_ligne(i)
                j_min = meilleure_colonne_de_ligne(i)
                cout_min = self.couts[i][j_min]
                q_possible = min(provisions_restantes[i], commandes_restantes[j_min])
                candidats.append(("ligne", i, p, j_min, cout_min, q_possible))

            for j in colonnes_actives:
                p = penalite_colonne(j)
                i_min = meilleure_ligne_de_colonne(j)
                cout_min = self.couts[i_min][j]
                q_possible = min(provisions_restantes[i_min], commandes_restantes[j])
                candidats.append(("colonne", j, p, i_min, cout_min, q_possible))

            # Priorité: pénalité max, coût min, quantité max.
            type_sel, idx_sel, pen_sel, idx_pair, cout_sel, q_sel = max(
                candidats,
                key=lambda x: (x[2], -x[4], x[5])
            )

            if type_sel == "ligne":
                i, j = idx_sel, idx_pair
            else:
                i, j = idx_pair, idx_sel

            quantite = min(provisions_restantes[i], commandes_restantes[j])
            self.transport[i][j] += quantite
            self.base.add((i, j))

            etapes.append(
                f"Pénalité max={pen_sel} sur {type_sel} {idx_sel}; "
                f"coût min={self.couts[i][j]} en (F{i}, C{j}), allocation={quantite}"
            )

            provisions_restantes[i] -= quantite
            commandes_restantes[j] -= quantite

            ligne_epuisee = provisions_restantes[i] == 0
            colonne_saturee = commandes_restantes[j] == 0

            if ligne_epuisee and colonne_saturee:
                # Cas dégénéré: retirer les deux et ajouter une cellule 0 à la base.
                lignes_actives.discard(i)
                colonnes_actives.discard(j)

                if lignes_actives:
                    i_alt = next(iter(lignes_actives))
                    self.base.add((i_alt, j))
                elif colonnes_actives:
                    j_alt = next(iter(colonnes_actives))
                    self.base.add((i, j_alt))
            elif ligne_epuisee:
                lignes_actives.discard(i)
            elif colonne_saturee:
                colonnes_actives.discard(j)

        if len(self.base) > self.n + self.m - 1:
            base_ordonnee = sorted(self.base)
            self.base = set(base_ordonnee[: self.n + self.m - 1])

        resultat = "\nMÉTHODE BALAS-HAMMER\n"
        resultat += "=" * 80 + "\n"
        for k, etape in enumerate(etapes, 1):
            resultat += f"{k:>2}. {etape}\n"
        resultat += "=" * 80 + "\n"
        resultat += f"Coût total obtenu: {self.cout_total()}\n"
        resultat += f"Taille de base: {len(self.base)} (attendu: {self.n + self.m - 1})"

        return resultat
    
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
