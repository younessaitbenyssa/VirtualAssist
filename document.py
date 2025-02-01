import customtkinter as ctk
from tkinter import filedialog, messagebox
import pymupdf
import os

class DocumentApp:
    def __init__(self, parent_frame):
        self.setup_ui(parent_frame)
        self.doc = None
        self.file_path = None
        self.highlights = []

    def setup_ui(self, parent_frame):
        self.main_container = ctk.CTkFrame(parent_frame)
        self.main_container.pack(fill="both", expand=True)
        
        self.toolbar = ctk.CTkFrame(self.main_container)
        self.toolbar.pack(fill="x", padx=5, pady=5)
        
        self.open_btn = ctk.CTkButton(self.toolbar, text="Ouvrir PDF", command=self.open_file)
        self.open_btn.pack(side="left", padx=5)
        
        self.save_btn = ctk.CTkButton(self.toolbar, text="Enregistrer PDF", command=self.save_pdf)
        self.save_btn.pack(side="left", padx=5)
        
        self.colors = ["yellow", "green", "blue", "red", "purple"]
        self.selected_color = ctk.StringVar(value=self.colors[0])
        self.color_menu = ctk.CTkOptionMenu(self.toolbar, values=self.colors, variable=self.selected_color)
        self.color_menu.pack(side="left", padx=5)
        
        self.text_widget = ctk.CTkTextbox(self.main_container)
        self.text_widget.pack(fill="both", expand=True)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.file_path = file_path
            self.load_pdf()

    def load_pdf(self):
        try:
            self.doc = pymupdf.open(self.file_path)
            text_content = ""
            for page in self.doc:
                text_content += page.get_text()
            self.text_widget.delete("1.0", "end")
            self.text_widget.insert("1.0", text_content)
            self.highlights = []
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur de lecture: {str(e)}")

    def save_pdf(self):
        if not self.file_path:
            messagebox.showwarning("Attention", "Ouvrez d'abord un PDF")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"highlighted_{os.path.basename(self.file_path)}"
        )
        
        if save_path:
            try:
                doc = pymupdf.open(self.file_path)
                
                for tag in self.text_widget.tag_names():
                    if tag.startswith("highlight_"):
                        color = tag.split('_')[1]
                        ranges = self.text_widget.tag_ranges(tag)
                        
                        for i in range(0, len(ranges), 2):
                            start_pos = ranges[i]
                            end_pos = ranges[i+1]
                            
                            # Convertir les indices en positions de page
                            text_before = self.text_widget.get("1.0", start_pos)
                            text_length = len(text_before)
                            
                            # Trouver la page correspondante
                            current_length = 0
                            for page_num in range(len(doc)):
                                page = doc[page_num]
                                page_text = page.get_text()
                                if current_length + len(page_text) > text_length:
                                    # Créer le surlignage
                                    areas = page.search_for(self.text_widget.get(start_pos, end_pos))
                                    for rect in areas:
                                        highlight = page.add_highlight_annot(rect)
                                        highlight.set_colors({"stroke": self.get_rgb_color(color)})
                                        highlight.update()
                                    break
                                current_length += len(page_text)
                
                doc.save(save_path)
                doc.close()
                messagebox.showinfo("Succès", "PDF enregistré avec les surlignages")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'enregistrement: {str(e)}")

    def get_rgb_color(self, color_name):
        colors = {
            "yellow": (1, 1, 0),
            "green": (0, 1, 0),
            "blue": (0, 0, 1),
            "red": (1, 0, 0),
            "purple": (0.5, 0, 0.5)
        }
        return colors.get(color_name, (1, 1, 0))

    def highlight_selected_text(self):
        if self.text_widget.tag_ranges("sel"):
            start = self.text_widget.index("sel.first")
            end = self.text_widget.index("sel.last")
            color = self.selected_color.get()
            tag_name = f"highlight_{color}"
            self.text_widget.tag_add(tag_name, start, end)
            self.text_widget.tag_config(tag_name, background=color)
