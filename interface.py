"""
Interface Tkinter pour le problème de transport.
Permet de charger un problème, afficher les matrices et exécuter les algorithmes.
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
from structure import ProblemeTransport


# Variables globales
probleme_actuel = None


def charger_probleme():
    """Charge un problème de transport depuis un fichier"""
    global probleme_actuel
    
    try:
        numero = entry_numero.get().strip()
        if not numero:
            messagebox.showwarning("Attention", "Entrez un numéro de problème.")
            return
        
        nom_fichier = f"transport{numero}.txt"
        probleme_actuel = ProblemeTransport.charger_depuis_fichier(nom_fichier)
        
        # Afficher le problème chargé
        affichage = f"✓ Problème {numero} chargé avec succès !\n"
        affichage += f"  Fournisseurs: {probleme_actuel.n}\n"
        affichage += f"  Clients: {probleme_actuel.m}\n"
        affichage += f"  Total provisions: {sum(probleme_actuel.provisions)}\n"
        affichage += f"  Total commandes: {sum(probleme_actuel.commandes)}\n"
        affichage += "\n"
        affichage += probleme_actuel.afficher_matrice_couts()
        
        text_output.config(state=tk.NORMAL)
        text_output.delete(1.0, tk.END)
        text_output.insert(tk.END, affichage)
        text_output.config(state=tk.DISABLED)
        
        # Activer boutons d'algorithmes
        button_nord_ouest.config(state=tk.NORMAL)
        button_balas_hammer.config(state=tk.NORMAL)
        
    except FileNotFoundError:
        messagebox.showerror("Erreur", f"Fichier 'transport{numero}.txt' non trouvé")
    except ValueError as e:
        messagebox.showerror("Erreur", f"Erreur de lecture: {e}")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur: {e}")


def afficher_cout_total():
    """Affiche le coût total du transport actuel"""
    global probleme_actuel
    
    if probleme_actuel is None:
        messagebox.showwarning("Attention", "Chargez d'abord un problème.")
        return
    
    cout = probleme_actuel.cout_total()
    texte_actuel = text_output.get(1.0, tk.END)
    
    affichage_cout = f"\n{'='*100}\nCOÛT TOTAL DU TRANSPORT: {cout}\n{'='*100}\n"
    
    text_output.config(state=tk.NORMAL)
    text_output.insert(tk.END, affichage_cout)
    text_output.config(state=tk.DISABLED)
    text_output.see(tk.END)


def afficher_matrice_transport():
    """Affiche la matrice de transport"""
    global probleme_actuel
    
    if probleme_actuel is None:
        messagebox.showwarning("Attention", "Chargez d'abord un problème.")
        return
    
    affichage = probleme_actuel.afficher_matrice_transport()
    
    text_output.config(state=tk.NORMAL)
    text_output.insert(tk.END, affichage + "\n")
    text_output.config(state=tk.DISABLED)
    text_output.see(tk.END)


def nouveau_probleme():
    """Réinitialise les données"""
    global probleme_actuel
    
    probleme_actuel = None
    entry_numero.delete(0, tk.END)
    
    text_output.config(state=tk.NORMAL)
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, "Entrez le numéro d'un problème de transport (ex: 1, 2, ..., 12)")
    text_output.config(state=tk.DISABLED)
    
    button_nord_ouest.config(state=tk.DISABLED)
    button_balas_hammer.config(state=tk.DISABLED)


# ========== CRÉATION FENÊTRE PRINCIPALE ==========
root = tk.Tk()
root.title("Problème de Transport - Recherche Opérationnelle")
root.geometry("1100x800")

# ========== FRAME CONTRÔLES ==========
frame_controls = tk.Frame(root, bg="#e8f4f8", pady=10)
frame_controls.pack(side=tk.TOP, fill=tk.X)

label_numero = tk.Label(frame_controls, text="Problème n°:", bg="#e8f4f8", font=("Arial", 10))
label_numero.pack(side=tk.LEFT, padx=5)

entry_numero = tk.Entry(frame_controls, width=5, font=("Arial", 10))
entry_numero.pack(side=tk.LEFT, padx=5)
entry_numero.bind('<Return>', lambda e: charger_probleme())

button_charger = tk.Button(frame_controls, text="Charger", command=charger_probleme, bg="#4CAF50", fg="white", font=("Arial", 9))
button_charger.pack(side=tk.LEFT, padx=5)

button_nord_ouest = tk.Button(frame_controls, text="Nord-Ouest", command=lambda: messagebox.showinfo("Info", "À implémenter"), 
                               state=tk.DISABLED, bg="#2196F3", fg="white", font=("Arial", 9))
button_nord_ouest.pack(side=tk.LEFT, padx=5)

button_balas_hammer = tk.Button(frame_controls, text="Balas-Hammer", command=lambda: messagebox.showinfo("Info", "À implémenter"), 
                                 state=tk.DISABLED, bg="#2196F3", fg="white", font=("Arial", 9))
button_balas_hammer.pack(side=tk.LEFT, padx=5)

button_afficher_transport = tk.Button(frame_controls, text="Afficher transport", command=afficher_matrice_transport, 
                                      bg="#FF9800", fg="white", font=("Arial", 9))
button_afficher_transport.pack(side=tk.LEFT, padx=5)

button_cout = tk.Button(frame_controls, text="Coût total", command=afficher_cout_total, 
                        bg="#FF9800", fg="white", font=("Arial", 9))
button_cout.pack(side=tk.LEFT, padx=5)

button_nouveau = tk.Button(frame_controls, text="Nouveau", command=nouveau_probleme, 
                           bg="#f44336", fg="white", font=("Arial", 9))
button_nouveau.pack(side=tk.LEFT, padx=5)

# ========== TEXT OUTPUT ==========
text_output = scrolledtext.ScrolledText(root, height=35, width=135, font=("Courier New", 9))
text_output.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
text_output.config(state=tk.DISABLED)

text_output.insert(tk.END, "Bienvenue ! Chargez un problème de transport (1-12)")
text_output.config(state=tk.DISABLED)

# ========== LANCEMENT ==========
root.mainloop()