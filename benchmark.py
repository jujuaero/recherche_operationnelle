"""
Script de benchmark des algorithmes de transport.
Exécute les 4 algorithmes sur des milliers de cas aléatoires et analyse la complexité.
"""

import time
import pandas as pd
from pathlib import Path
from generateur import generer_fichier_transport
from structure import ProblemeTransport


class BenchmarkTransport:
    """Gère l'orchestration et l'analyse des tests de performance"""
    
    def __init__(self, fichier_csv="resultats_benchmark.csv"):
        self.fichier_csv = fichier_csv
        self.donnees = self._charger_ou_creer()
    
    def _charger_ou_creer(self):
        """Crée ou recharge le CSV existant"""
        if Path(self.fichier_csv).exists():
            print(f"[OK] Fichier '{self.fichier_csv}' trouve, continuer les tests...")
            df = pd.read_csv(self.fichier_csv)
            # Assurer que les colonnes numériques sont bien typées
            df['temps_ms'] = pd.to_numeric(df['temps_ms'], errors='coerce')
            df['cout_total'] = pd.to_numeric(df['cout_total'], errors='coerce')
            df['base_size'] = pd.to_numeric(df['base_size'], errors='coerce')
            df['validations_ok'] = df['validations_ok'].astype(bool)
            # Ajouter colonne initialisation si elle n'existe pas
            if 'initialisation' not in df.columns:
                df['initialisation'] = df['algorithme'].apply(
                    lambda x: 'nord_ouest' if x == 'marche_pied' else None
                )
            return df
        
        print(f"[OK] Creation d'un nouveau fichier '{self.fichier_csv}'...")
        df = pd.DataFrame(columns=[
            'test_id', 'n', 'm', 'algorithme', 'initialisation',
            'temps_ms', 'cout_total', 'base_size',
            'validations_ok', 'timestamp'
        ])
        # Initialiser avec les bons types
        df = df.astype({
            'test_id': 'int64',
            'n': 'int64',
            'm': 'int64',
            'algorithme': 'object',
            'temps_ms': 'float64',
            'cout_total': 'float64',
            'base_size': 'int64',
            'validations_ok': 'bool',
            'timestamp': 'object'
        })
        return df
    
    def _generer_probleme(self, n, m):
        """Génère un problème de transport aléatoire"""
        nom_fichier = f"temp_{n}x{m}_{time.time()}.txt"
        generer_fichier_transport(n, m, nom_fichier)
        probleme = ProblemeTransport.charger_depuis_fichier(nom_fichier)
        return probleme
    
    def _valider_solution(self, probleme):
        """Vérifie que la solution respecte toutes les conditions"""
        erreurs = []
        
        # 1. Taille de base
        if len(probleme.base) != probleme.n + probleme.m - 1:
            erreurs.append(f"Base: {len(probleme.base)} ≠ {probleme.n + probleme.m - 1}")
        
        # 2. Provisions respectées
        for i in range(probleme.n):
            if sum(probleme.transport[i]) != probleme.provisions[i]:
                erreurs.append(f"F{i}: sum={sum(probleme.transport[i])} ≠ {probleme.provisions[i]}")
        
        # 3. Commandes respectées
        for j in range(probleme.m):
            col_sum = sum(probleme.transport[i][j] for i in range(probleme.n))
            if col_sum != probleme.commandes[j]:
                erreurs.append(f"C{j}: sum={col_sum} ≠ {probleme.commandes[j]}")
        
        # 4. Non-négativité
        for i in range(probleme.n):
            for j in range(probleme.m):
                if probleme.transport[i][j] < 0:
                    erreurs.append(f"({i},{j}): négatif = {probleme.transport[i][j]}")
        
        return len(erreurs) == 0, erreurs
    
    def ajouter_resultat(self, n, m, algo, temps_ms, cout, base_size, validations_ok, initialisation=None):
        """Ajoute une ligne et sauvegarde incrémentalement"""
        nouveau = pd.DataFrame([{
            'test_id': len(self.donnees),
            'n': n,
            'm': m,
            'algorithme': algo,
            'initialisation': initialisation,
            'temps_ms': temps_ms,
            'cout_total': cout,
            'base_size': base_size,
            'validations_ok': validations_ok,
            'timestamp': pd.Timestamp.now()
        }])
        self.donnees = pd.concat([self.donnees, nouveau], ignore_index=True)
        self._sauvegarder()
    
    def _sauvegarder(self):
        """Sauvegarde incrémentale au CSV"""
        self.donnees.to_csv(self.fichier_csv, index=False)
    
    def executer_test(self, n, m, algorithme, probleme, initialisation=None):
        """Exécute un algorithme et retourne temps + cout"""
        # Recopier le problème pour chaque algo
        prob = ProblemeTransport()
        prob.n = probleme.n
        prob.m = probleme.m
        prob.couts = [row[:] for row in probleme.couts]
        prob.provisions = probleme.provisions[:]
        prob.commandes = probleme.commandes[:]
        prob.transport = [[0] * m for _ in range(n)]
        prob.base = set()
        
        # Exécuter l'algorithme avec timing
        debut = time.perf_counter()
        max_iterations_marche_pied = max(1000, n * m * 20)
        
        try:
            if algorithme == "nord_ouest":
                prob.methode_nord_ouest()
            elif algorithme == "balas_hammer":
                prob.methode_balas_hammer()
            elif algorithme == "marche_pied":
                # Initialiser selon le paramètre
                if initialisation == "balas_hammer":
                    prob.methode_balas_hammer()
                else:  # par défaut nord_ouest
                    prob.methode_nord_ouest()
                prob.methode_marche_pied_potentiels(
                    methode_initiale=initialisation or "nord_ouest",
                    max_iterations=max_iterations_marche_pied,
                )
            
            temps_ms = (time.perf_counter() - debut) * 1000
            cout = prob.cout_total()
            base_size = len(prob.base)
            
            # Valider la solution
            validations_ok, erreurs = self._valider_solution(prob)
            if not validations_ok:
                print(f"  [WARNING] Validation ECHOUEE ({algorithme}, {n}x{m}): {erreurs[0]}")
            
            return temps_ms, cout, base_size, validations_ok
        
        except Exception as e:
            print(f"  [ERROR] Erreur lors de {algorithme} ({n}x{m}): {str(e)[:50]}")
            return None, None, None, False
    
    def lancer_campagne(self, configs_dim, nb_tests_par_config=1000):
        """
        Lance une campagne de tests sur plusieurs dimensions et algorithmes.
        
        Args:
            configs_dim: liste de tuples (n, m) à tester
            nb_tests_par_config: nombre d'itérations par (n, m, algo) triplet
        """
        algos = ["nord_ouest", "balas_hammer"]
        marche_pied_inits = ["nord_ouest", "balas_hammer"]
        total_tests = len(configs_dim) * (len(algos) + len(marche_pied_inits)) * nb_tests_par_config
        test_num = 0
        
        print(f"\n{'='*80}")
        print(f"CAMPAGNE DE BENCHMARK")
        print(f"{'='*80}")
        print(f"Configurations: {configs_dim}")
        print(f"Iterations par (n, m, algo): {nb_tests_par_config}")
        print(f"Total de tests: {total_tests}")
        print(f"Sauvegarde: {self.fichier_csv}\n")
        
        for n, m in configs_dim:
            print(f"\n--- Configuration {n} x {m} ---")

            success_counts = {
                "nord_ouest": 0,
                "balas_hammer": 0,
                "marche_pied_nord_ouest": 0,
                "marche_pied_balas_hammer": 0,
            }

            for test_nbr in range(nb_tests_par_config):
                # Une seule instance par iteration, partagee entre tous les algos.
                try:
                    prob = self._generer_probleme(n, m)
                except Exception as e:
                    print(f"\n  [ERROR] Generation echouee: {str(e)[:30]}")
                    continue

                # Algorithmes de base
                for algo in algos:
                    test_num += 1
                    temps, cout, base_size, valid_ok = self.executer_test(n, m, algo, prob)

                    if temps is not None:
                        self.ajouter_resultat(n, m, algo, temps, cout, base_size, valid_ok)
                        if valid_ok:
                            success_counts[algo] += 1

                # Marche pied avec differentes initialisations
                for init in marche_pied_inits:
                    test_num += 1
                    temps, cout, base_size, valid_ok = self.executer_test(
                        n, m, "marche_pied", prob, initialisation=init
                    )

                    if temps is not None:
                        self.ajouter_resultat(
                            n, m, "marche_pied", temps, cout, base_size, valid_ok, initialisation=init
                        )
                        if valid_ok:
                            success_counts[f"marche_pied_{init}"] += 1

                if (test_nbr + 1) % 100 == 0:
                    print(f"  progression: {test_nbr + 1}/{nb_tests_par_config}", flush=True)

            print(f"  nord_ouest: [OK] ({success_counts['nord_ouest']}/{nb_tests_par_config} valides)")
            print(f"  balas_hammer: [OK] ({success_counts['balas_hammer']}/{nb_tests_par_config} valides)")
            print(
                f"  marche_pied (init:nord_ouest): [OK] "
                f"({success_counts['marche_pied_nord_ouest']}/{nb_tests_par_config} valides)"
            )
            print(
                f"  marche_pied (init:balas_hammer): [OK] "
                f"({success_counts['marche_pied_balas_hammer']}/{nb_tests_par_config} valides)"
            )
        
        print(f"\n{'='*80}")
        print(f"Benchmark termine !")
        print(f"Resultats sauvegardes dans '{self.fichier_csv}'")
        print(f"{'='*80}\n")
    
    def analyser(self):
        """Analyse et affiche les résultats"""
        if len(self.donnees) == 0:
            print("Aucune donnée à analyser.")
            return
        
        print(f"\n{'='*80}")
        print("ANALYSE DES RÉSULTATS")
        print(f"{'='*80}\n")
        
        # 1. Statistiques globales par algorithme et dimension
        print("1. TEMPS MOYEN (ms) par configuration et algorithme:\n")
        pivot_temps = self.donnees.groupby(['n', 'm', 'algorithme'])['temps_ms'].agg(['mean', 'std', 'min', 'max']).round(4)
        print(pivot_temps)
        
        # 2. Taux de validation
        print("\n\n2. TAUX DE VALIDATION (solutions valides):\n")
        taux_valid = self.donnees.groupby(['n', 'm', 'algorithme'])['validations_ok'].apply(
            lambda x: f"{(x.sum()/len(x)*100):.1f}%"
        )
        print(taux_valid)
        
        # 3. Comparaison de qualité (coût moyen)
        print("\n\n3. COÛT MOYEN par algorithme et configuration:\n")
        pivot_cout = self.donnees.groupby(['n', 'm', 'algorithme'])['cout_total'].mean().round(2)
        print(pivot_cout)
        
        # 4. Ratio de temps (pour étudier complexité)
        print("\n\n4. RATIO TEMPS par rapport à Nord-Ouest:\n")
        for (n, m), group in self.donnees.groupby(['n', 'm']):
            print(f"\n{n} × {m}:")
            temps_nw = group[group['algorithme'] == 'nord_ouest']['temps_ms'].mean()
            for algo in ['balas_hammer', 'marche_pied']:
                temps_algo = group[group['algorithme'] == algo]['temps_ms'].mean()
                if temps_nw > 0:
                    ratio = temps_algo / temps_nw
                    print(f"  {algo}: {ratio:.2f}x plus lent")
        
        # 5. Exporter en CSV pour traitement ultérieur
        print("\n\nDonnées disponibles pour Excel/R/Python :")
        print(f"  -> {self.fichier_csv}")


def main():
    """Fonction principale d'exécution"""
    import sys
    
    # Configuration des tests
    configs = [
        (5, 5),
        (5, 10),
        (10, 5),
        (10, 10),
        (15, 15),
        (20, 20),
    ]
    
    nb_tests = 100  # Augmentez à 1000+ pour analyse complète
    
    if len(sys.argv) > 1:
        try:
            nb_tests = int(sys.argv[1])
        except:
            print("Usage: python benchmark.py [nombre_de_tests]")
            sys.exit(1)
    
    # Lancer la campagne
    bench = BenchmarkTransport()
    bench.lancer_campagne(configs, nb_tests_par_config=nb_tests)
    
    # Analyser les résultats
    bench.analyser()


if __name__ == "__main__":
    main()
