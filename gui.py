import tkinter as tk
from tkinter import filedialog
from parser_pdf import estrai_dati_da_pdf


def avvia_gui():
    root = tk.Tk()
    root.title("Parser PDF Cedolino Stipendiale")
    root.geometry("900x600")

    # ======================
    # PANED WINDOW (DIVISORE TRASCINABILE)
    # ======================
    paned = tk.PanedWindow(root, orient=tk.VERTICAL)
    paned.pack(fill=tk.BOTH, expand=True)

    # ======================
    # PARTE SUPERIORE (GIALLA – SELEZIONABILE)
    # ======================
    top_container = tk.Frame(paned, bg="#ffe600")
    paned.add(top_container, height=200)

    top_scroll = tk.Scrollbar(top_container)
    top_scroll.pack(side="right", fill="y")

    riepilogo = tk.Text(
        top_container,
        bg="#ffe600",
        wrap="word",
        height=10,
        yscrollcommand=top_scroll.set
    )
    riepilogo.pack(side="left", fill="both", expand=True)

    top_scroll.config(command=riepilogo.yview)

    # rende il Text solo leggibile
    riepilogo.config(state="disabled")

    # ======================
    # PARTE INFERIORE (VOCI SCROLLABILI)
    # ======================
    bottom_container = tk.Frame(paned)
    paned.add(bottom_container)

    canvas = tk.Canvas(bottom_container)
    scrollbar = tk.Scrollbar(bottom_container, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    checks = []
    dati_correnti = {}

    # ======================
    # FUNZIONI
    # ======================
    def aggiorna_riepilogo():
        riepilogo.config(state="normal")
        riepilogo.delete("1.0", tk.END)

        riepilogo.insert(tk.END, f"NOMINATIVO: {dati_correnti.get('nominativo','')}\n")
        riepilogo.insert(tk.END, f"MATRICOLA: {dati_correnti.get('matricola','')}\n")
        riepilogo.insert(tk.END, f"CF: {dati_correnti.get('cf','')}\n")
        riepilogo.insert(tk.END, f"PERIODO: {dati_correnti.get('periodo','')}\n\n")

        totale = 0.0
        riepilogo.insert(tk.END, "VOCI SELEZIONATE:\n")

        for var, voce in checks:
            if var.get():
                riepilogo.insert(
                    tk.END,
                    f"- {voce['descrizione']} € {voce['importo']:.2f}\n"
                )
                totale += voce["importo"]

        riepilogo.insert(
            tk.END,
            f"\nTOTALE SELEZIONATO: € {totale:.2f}"
        )

        riepilogo.config(state="disabled")

    def carica_pdf():
        nonlocal dati_correnti
        path = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")])
        if not path:
            return

        dati_correnti = estrai_dati_da_pdf(path)

        for w in scroll_frame.winfo_children():
            w.destroy()
        checks.clear()

        for voce in dati_correnti["voci"]:
            var = tk.BooleanVar(value=False)  # NON selezionate di default
            cb = tk.Checkbutton(
                scroll_frame,
                text=f"{voce['descrizione']} € {voce['importo']:.2f}",
                variable=var,
                command=aggiorna_riepilogo
            )
            cb.pack(anchor="w")
            checks.append((var, voce))

        aggiorna_riepilogo()

    # ======================
    # BOTTONE CARICA PDF
    # ======================
    tk.Button(root, text="Carica PDF", command=carica_pdf).pack(pady=5)

    root.mainloop()
