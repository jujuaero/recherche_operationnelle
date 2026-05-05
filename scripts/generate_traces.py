"""
Générateur de traces pour les 12 problèmes de transport.
Exécute Nord-Ouest et Balas-Hammer + marche-pied potentiels pour chaque problème.
Génère des fichiers de traces au format: groupe-equipe-traceproblem-methode.txt
"""

from pathlib import Path
import sys
from structure import ProblemeTransport

# Configuration: mapping problème -> (groupe, équipe)
# Groupe 5, Équipe 2 pour tous les problèmes
MAPPING_GROUPE_EQUIPE = {
    i: (
        5,                      # groupe (toujours 5)
        2                       # équipe (toujours 2)
    )
    for i in range(1, 13)
}

# Vous pouvez personnaliser le mapping ici si nécessaire
# Exemple: MAPPING_GROUPE_EQUIPE[5] = (2, 4)  # pour l'exemple "2-4-trace5-no.txt"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRACES_DIR = PROJECT_ROOT / "results" / "traces"
TRACES_DIR.mkdir(parents=True, exist_ok=True)

def generer_traces():
    """Génère les traces pour les 12 problèmes."""
    
    total_problemes = 12
    success_count = 0
    error_messages = []
    
    for num_probleme in range(1, total_problemes + 1):
        groupe, equipe = MAPPING_GROUPE_EQUIPE[num_probleme]
        nom_fichier = f"transport{num_probleme}.txt"
        
        print(f"\n{'='*80}")
        print(f"Traitement Problème {num_probleme} (Groupe {groupe}, Équipe {equipe})")
        print(f"{'='*80}")
        
        try:
            # Charger le problème
            probleme = ProblemeTransport.charger_depuis_fichier(nom_fichier)
            print(f"✓ Problème {num_probleme} chargé avec succès")
            print(f"  Fournisseurs: {probleme.n}, Clients: {probleme.m}")
            
            # ==================== NORD-OUEST ====================
            print(f"\n[1/2] Exécution Nord-Ouest + marche-pied potentiels...")
            
            traces_no = f"\n{'#'*80}\n"
            traces_no += f"# GROUPE {groupe} - ÉQUIPE {equipe} - PROBLÈME {num_probleme}\n"
            traces_no += f"# MÉTHODE: NORD-OUEST (NO)\n"
            traces_no += f"{'#'*80}\n"
            
            # Afficher le problème
            traces_no += f"\n{probleme.afficher_matrice_couts()}\n"
            
            # Exécuter marche-pied avec initialisationNord-Ouest
            resultat_no = probleme.methode_marche_pied_potentiels(
                methode_initiale="nord_ouest",
                max_iterations=1000
            )
            traces_no += resultat_no
            traces_no += f"\n\nCoût final: {probleme.cout_total()}\n"
            traces_no += f"Matrice de transport finale:\n{probleme.afficher_matrice_transport()}\n"
            
            # Sauvegarder le fichier NO
            nom_fichier_no = f"{groupe}-{equipe}-trace{num_probleme}-no.txt"
            chemin_no = TRACES_DIR / nom_fichier_no
            chemin_no.write_text(traces_no, encoding='utf-8')
            print(f"✓ Fichier créé: {nom_fichier_no}")
            
            # ==================== BALAS-HAMMER ====================
            print(f"\n[2/2] Exécution Balas-Hammer + marche-pied potentiels...")
            
            # Recharger le problème pour réinitialiser l'état
            probleme = ProblemeTransport.charger_depuis_fichier(nom_fichier)
            
            traces_bh = f"\n{'#'*80}\n"
            traces_bh += f"# GROUPE {groupe} - ÉQUIPE {equipe} - PROBLÈME {num_probleme}\n"
            traces_bh += f"# MÉTHODE: BALAS-HAMMER (BH)\n"
            traces_bh += f"{'#'*80}\n"
            
            # Afficher le problème
            traces_bh += f"\n{probleme.afficher_matrice_couts()}\n"
            
            # Exécuter marche-pied avec initialisation Balas-Hammer
            resultat_bh = probleme.methode_marche_pied_potentiels(
                methode_initiale="balas_hammer",
                max_iterations=1000
            )
            traces_bh += resultat_bh
            traces_bh += f"\n\nCoût final: {probleme.cout_total()}\n"
            traces_bh += f"Matrice de transport finale:\n{probleme.afficher_matrice_transport()}\n"
            
            # Sauvegarder le fichier BH
            nom_fichier_bh = f"{groupe}-{equipe}-trace{num_probleme}-bh.txt"
            chemin_bh = TRACES_DIR / nom_fichier_bh
            chemin_bh.write_text(traces_bh, encoding='utf-8')
            print(f"✓ Fichier créé: {nom_fichier_bh}")
            
            success_count += 1
            
        except Exception as e:
            msg = f"✗ Erreur Problème {num_probleme}: {str(e)}"
            print(msg)
            error_messages.append(msg)
    
    # Résumé final
    print(f"\n{'='*80}")
    print(f"RÉSUMÉ")
    print(f"{'='*80}")
    print(f"Succès: {success_count}/{total_problemes} problèmes traités")
    print(f"Fichiers créés: {success_count * 2}/24 fichiers de traces")
    print(f"Dossier de sortie: {TRACES_DIR}")
    
    if error_messages:
        print(f"\nErreurs rencontrées:")
        for msg in error_messages:
            print(f"  {msg}")
    
    return success_count == total_problemes

if __name__ == "__main__":
    success = generer_traces()
    sys.exit(0 if success else 1)
