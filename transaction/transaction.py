import customtkinter as ctk
from tkinter import messagebox, ttk
import csv
from datetime import datetime
import matplotlib.pyplot as plt
from collections import defaultdict
import os
from PIL import Image, ImageTk
from tkcalendar import DateEntry
from fpdf import FPDF

# Configuration de l'apparence
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Fichier pour stocker les catégories
CATEGORIES_FILE = "categories.txt"

class TransactionApp:
    def __init__(self, parent_frame):
        self.transactions = []
        self.balance = 0.0
        self.total_entrees = 0.0
        self.total_sorties = 0.0
        self.categories = self.load_categories()
        self.threshold = 1000.0  # Seuil prédéfini pour les alertes
        self.main_container = ctk.CTkFrame(parent_frame)
        self.main_container.pack(side="right", fill="both", expand=True)

        self.add_default_categories()
        self.create_widgets()

    def load_categories(self):
        """Charge les catégories depuis le fichier."""
        if os.path.exists(CATEGORIES_FILE):
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as file:
                return [line.strip() for line in file.readlines()]
        return []

    def save_categories(self):
        """Sauvegarde les catégories dans le fichier."""
        with open(CATEGORIES_FILE, "w", encoding="utf-8") as file:
            for category in self.categories:
                file.write(category + "\n")

    def add_default_categories(self):
        """Ajoute les catégories par défaut si elles n'existent pas."""
        default_categories = ["Achat", "Vente", "Crédit"]
        for category in default_categories:
            if category not in self.categories:
                self.categories.append(category)
        self.save_categories()

    def create_widgets(self):
        """Crée l'interface utilisateur."""
        self.main_container.configure(fg_color="#2E3440")

        # Cadre principal avec barre de défilement
        main_canvas = ctk.CTkCanvas(self.main_container, bg="#2E3440", highlightthickness=0)
        main_canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=main_canvas.yview)
        scrollbar.pack(side="right", fill="y")

        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        # Cadre intérieur
        inner_frame = ctk.CTkFrame(main_canvas, fg_color="#3B4252")
        main_canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        # Formulaire pour ajouter une transaction
        form_frame = ctk.CTkFrame(inner_frame, fg_color="#4C566A")
        form_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(form_frame, text="Montant :", text_color="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.amount_entry = ctk.CTkEntry(form_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Catégorie :", text_color="white").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.category_combobox = ctk.CTkComboBox(form_frame, values=self.categories)
        self.category_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Description :", text_color="white").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.description_entry = ctk.CTkEntry(form_frame)
        self.description_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(form_frame, text="Date :", text_color="white").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.date_entry = DateEntry(form_frame, date_pattern="yyyy-mm-dd")
        self.date_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.add_button = ctk.CTkButton(
            form_frame,
            text="Ajouter",
            command=self.add_transaction,
            compound="left"
        )
        self.add_button.grid(row=4, column=1, columnspan=2, pady=10)

        # Barre de recherche et filtre
        search_filter_frame = ctk.CTkFrame(form_frame, fg_color="#4C566A")
        search_filter_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        self.search_entry = ctk.CTkEntry(search_filter_frame, placeholder_text="Rechercher par description...", width=300)
        self.search_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.search_transactions)

        self.search_date_entry = DateEntry(search_filter_frame, date_pattern="yyyy-mm-dd", width=12)
        self.search_date_entry.pack(side="left", padx=5, pady=5)
        self.search_date_entry.bind("<KeyRelease>", self.search_transactions)

        self.reset_button = ctk.CTkButton(
            search_filter_frame,
            text="Réinitialiser",
            command=self.reset_search,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.reset_button.pack(side="left", padx=5, pady=5)

        self.filter_combobox = ctk.CTkComboBox(search_filter_frame, values=["Toutes"] + self.categories, command=self.filter_transactions, width=150)
        self.filter_combobox.pack(side="left", padx=5, pady=5)

        # Affichage du solde
        balance_frame = ctk.CTkFrame(inner_frame, fg_color="#4C566A")
        balance_frame.pack(fill="x", padx=10, pady=10)

        self.sorties_label = ctk.CTkLabel(
            balance_frame,
            text=f"Sorties : {self.total_sorties} DH",
            font=("Arial", 14, "bold"),
            text_color="white",
            fg_color="red",
            corner_radius=10
        )
        self.sorties_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.total_label = ctk.CTkLabel(
            balance_frame,
            text=f"Total : {self.balance} DH",
            font=("Arial", 14, "bold"),
            text_color="white",
            fg_color="black",
            corner_radius=10
        )
        self.total_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.entrees_label = ctk.CTkLabel(
            balance_frame,
            text=f"Entrées : {self.total_entrees} DH",
            font=("Arial", 14, "bold"),
            text_color="white",
            fg_color="green",
            corner_radius=10
        )
        self.entrees_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Historique des transactions
        history_frame = ctk.CTkFrame(inner_frame, fg_color="#4C566A")
        history_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.history_tree = ttk.Treeview(
            history_frame,
            columns=("Date", "Montant", "Catégorie", "Description"),
            show="headings",
            style="Custom.Treeview"
        )
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Montant", text="Montant (DH)")
        self.history_tree.heading("Catégorie", text="Catégorie")
        self.history_tree.heading("Description", text="Description")
        self.history_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar_y = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.history_tree.configure(yscrollcommand=scrollbar_y.set)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview", font=("Arial", 10), rowheight=25, background="#4C566A", fieldbackground="#4C566A", foreground="white")
        style.configure("Custom.Treeview.Heading", font=("Arial", 10, "bold"), background="#4CAF50", foreground="white")
        style.map("Custom.Treeview", background=[("selected", "#4CAF50")])

        # Boutons d'actions
        button_frame = ctk.CTkFrame(inner_frame, fg_color="#4C566A")
        button_frame.pack(fill="x", padx=10, pady=10)

        self.export_button = ctk.CTkButton(
            button_frame,
            text="Exporter en CSV",
            command=self.export_to_csv,
            compound="left"
        )
        self.export_button.grid(row=0, column=0, padx=5)

        self.chart_button = ctk.CTkButton(
            button_frame,
            text="Afficher Graphique",
            command=self.show_category_chart,
            compound="left"
        )
        self.chart_button.grid(row=0, column=1, padx=5)

        self.pdf_button = ctk.CTkButton(
            button_frame,
            text="Télécharger en PDF",
            command=self.export_to_pdf,
            fg_color="#4CAF50",
            hover_color="red",
            compound="left"
        )
        self.pdf_button.grid(row=0, column=2, padx=5)

    def add_transaction(self):
        """Ajoute une transaction à la liste."""
        try:
            amount = float(self.amount_entry.get())
            category = self.category_combobox.get()
            description = self.description_entry.get()
            date = self.date_entry.get_date().strftime("%Y-%m-%d")

            # Vérifier si la date est antérieure à la date actuelle
            if datetime.strptime(date, "%Y-%m-%d").date() < datetime.now().date():
                messagebox.showerror("Erreur", "La date ne peut pas être antérieure à la date actuelle.")
                return

            if category in ["Achat", "Crédit"]:
                self.total_sorties += amount
                self.balance -= amount
            elif category == "Vente":
                self.total_entrees += amount
                self.balance += amount
            else:
                messagebox.showwarning("Avertissement", "Catégorie non reconnue. Utilisez 'Achat', 'Vente' ou 'Crédit'.")
                return

            self.transactions.append({
                "date": date,
                "amount": amount,
                "category": category,
                "description": description
            })

            self.sorties_label.configure(text=f"Sorties : {self.total_sorties} DH")
            self.entrees_label.configure(text=f"Entrées : {self.total_entrees} DH")
            self.total_label.configure(text=f"Total : {self.balance} DH")

            self.update_history()

            self.amount_entry.delete(0, "end")
            self.description_entry.delete(0, "end")

            # Vérifier le solde après chaque transaction
            self.check_balance()
            # Vérifier si la dépense dépasse un seuil prédéfini
            self.check_threshold(amount)

        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer un montant valide.")

    def check_balance(self):
        """Vérifie si le solde est négatif et affiche une alerte."""
        if self.balance < 0:
            messagebox.showwarning("Alerte", "Votre solde est négatif !")
            self.total_label.configure(fg_color="red")  # Changer la couleur du fond en rouge
        else:
            self.total_label.configure(fg_color="black")  # Revenir à la couleur par défaut

    def check_threshold(self, amount):
        """Vérifie si la dépense dépasse un seuil prédéfini et affiche une alerte."""
        if amount > self.threshold:
            messagebox.showwarning("Alerte", f"La dépense dépasse le seuil de {self.threshold} DH !")
            self.sorties_label.configure(fg_color="orange")  # Changer la couleur du fond en orange
        else:
            self.sorties_label.configure(fg_color="red")  # Revenir à la couleur par défaut

    def update_history(self, transactions=None):
        """Met à jour l'historique des transactions."""
        if transactions is None:
            transactions = self.transactions

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        for transaction in transactions:
            self.history_tree.insert("", "end", values=(
                transaction["date"],
                transaction["amount"],
                transaction["category"],
                transaction["description"]
            ))

    def filter_transactions(self, category):
        """Filtre les transactions par catégorie."""
        if category == "Toutes":
            self.update_history()
        else:
            filtered_transactions = [t for t in self.transactions if t["category"] == category]
            self.update_history(filtered_transactions)

    def search_transactions(self, event=None):
        """
        Recherche des transactions en fonction de la description et/ou de la date.
        Si seul un critère est saisi, il est utilisé pour filtrer les transactions.
        """
        # Récupérer les critères de recherche
        search_term = self.search_entry.get().lower()  # Terme de recherche (description)
        search_date = self.search_date_entry.get_date()  # Date sélectionnée

        # Convertir la date en chaîne de caractères si elle existe
        search_date_str = search_date.strftime("%Y-%m-%d") if search_date else None

        # Filtrer les transactions en fonction des critères de recherche
        filtered_transactions = []
        for transaction in self.transactions:
            # Vérifier si la description correspond (si un terme de recherche est saisi)
            match_description = (search_term in transaction["description"].lower()) if search_term else True

            # Vérifier si la date correspond (si une date est sélectionnée)
            match_date = (search_date_str == transaction["date"]) if search_date_str else True

            # Si au moins un critère est rempli, ajouter la transaction aux résultats
            if match_description and match_date:
                filtered_transactions.append(transaction)

        # Mettre à jour l'historique avec les transactions filtrées
        self.update_history(filtered_transactions)

        # Afficher un message si aucune transaction ne correspond aux critères
        if not filtered_transactions:
            messagebox.showinfo("Recherche", "Aucune transaction ne correspond aux critères de recherche.")

        # Debug : Afficher les résultats de la recherche dans la console
        print(f"Terme de recherche : {search_term}")
        print(f"Date de recherche : {search_date_str}")
        print(f"Transactions filtrées : {len(filtered_transactions)}")

    def reset_search(self):
        """Réinitialise la recherche et affiche toutes les transactions."""
        self.search_entry.delete(0, "end")
        self.search_date_entry.set_date(None)
        self.update_history()

    def export_to_csv(self):
        """Exporte les transactions au format CSV."""
        if not self.transactions:
            messagebox.showwarning("Avertissement", "Aucune transaction à exporter.")
            return

        with open("transactions.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Montant (DH)", "Catégorie", "Description"])
            for transaction in self.transactions:
                writer.writerow([
                    transaction["date"],
                    transaction["amount"],
                    transaction["category"],
                    transaction["description"]
                ])
        messagebox.showinfo("Export réussi", "Les transactions ont été exportées dans transactions.csv")

    def export_to_pdf(self):
        """Exporte les transactions au format PDF."""
        if not self.transactions:
            messagebox.showwarning("Avertissement", "Aucune transaction à exporter.")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Historique des Transactions", ln=True, align="C")

        pdf.set_font("Arial", size=10)
        pdf.cell(40, 10, txt="Date", border=1)
        pdf.cell(40, 10, txt="Montant (DH)", border=1)
        pdf.cell(40, 10, txt="Catégorie", border=1)
        pdf.cell(80, 10, txt="Description", border=1)
        pdf.ln()

        for transaction in self.transactions:
            pdf.cell(40, 10, txt=transaction["date"], border=1)
            pdf.cell(40, 10, txt=str(transaction["amount"]), border=1)
            pdf.cell(40, 10, txt=transaction["category"], border=1)
            pdf.cell(80, 10, txt=transaction["description"], border=1)
            pdf.ln()

        pdf.output("transactions.pdf")
        messagebox.showinfo("Export réussi", "Les transactions ont été exportées dans transactions.pdf")

    def show_category_chart(self):
        """Affiche un graphique des transactions par catégorie."""
        if not self.transactions:
            messagebox.showwarning("Avertissement", "Aucune transaction à afficher.")
            return

        category_totals = defaultdict(float)
        for transaction in self.transactions:
            category_totals[transaction["category"]] += 1

        categories = list(category_totals.keys())
        counts = list(category_totals.values())

        plt.figure(figsize=(8, 6))
        plt.pie(counts, labels=categories, autopct="%1.1f%%", startangle=140, colors=["#FF9999", "#66B2FF", "#99FF99"])
        plt.title("Répartition des Transactions par Catégorie", fontsize=16, fontweight="bold")
        plt.show()

