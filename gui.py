import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

from csv_to_txt import convert_csv_to_fixed_txt


def avvia_gui():
    root = tk.Tk()
    root.title("Convertitore CSV → TXT")
    root.geometry("700x500")

    csv_path_var = tk.StringVar()
    output_dir_var = tk.StringVar(value=os.getcwd())
    progressivo_var = tk.StringVar(value=datetime.now().strftime("%m%d%H%M%S"))

    container = tk.Frame(root, padx=20, pady=20)
    container.pack(fill=tk.BOTH, expand=True)

    tk.Label(container, text="File CSV").grid(row=0, column=0, sticky="w")
    csv_entry = tk.Entry(container, textvariable=csv_path_var, width=50)
    csv_entry.grid(row=0, column=1, padx=5, sticky="ew")

    def scegli_csv():
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv;*.CSV")])
        if path:
            csv_path_var.set(path)

    tk.Button(container, text="Scegli CSV", command=scegli_csv).grid(
        row=0, column=2, padx=5
    )

    tk.Label(container, text="Cartella output").grid(row=1, column=0, sticky="w")
    output_entry = tk.Entry(container, textvariable=output_dir_var, width=50)
    output_entry.grid(row=1, column=1, padx=5, sticky="ew")

    def scegli_cartella():
        path = filedialog.askdirectory()
        if path:
            output_dir_var.set(path)

    tk.Button(container, text="Scegli cartella", command=scegli_cartella).grid(
        row=1, column=2, padx=5
    )

    tk.Label(container, text="Progressivo (10 cifre)").grid(
        row=2, column=0, sticky="w"
    )
    tk.Entry(container, textvariable=progressivo_var, width=20).grid(
        row=2, column=1, sticky="w"
    )

    status = tk.Text(container, height=12, state="disabled")
    status.grid(row=4, column=0, columnspan=3, pady=15, sticky="nsew")

    def aggiorna_status(messaggio):
        status.config(state="normal")
        status.insert(tk.END, f"{messaggio}\n")
        status.see(tk.END)
        status.config(state="disabled")

    def converti():
        csv_path = csv_path_var.get().strip()
        output_dir = output_dir_var.get().strip()
        progressivo_raw = progressivo_var.get().strip()

        if not csv_path:
            messagebox.showerror("Errore", "Seleziona un file CSV.")
            return
        if not os.path.isfile(csv_path):
            messagebox.showerror("Errore", "Il file CSV selezionato non esiste.")
            return
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Errore", "Seleziona una cartella di output valida.")
            return
        if not progressivo_raw.isdigit():
            messagebox.showerror("Errore", "Il progressivo deve essere numerico.")
            return

        progressivo = int(progressivo_raw)
        filename = f"IRMEQS{datetime.now().year}{progressivo:010}.TXT"
        txt_path = os.path.join(output_dir, filename)

        try:
            aggiorna_status(f"Conversione in corso: {os.path.basename(csv_path)}")
            convert_csv_to_fixed_txt(csv_path, txt_path, progressivo)
            aggiorna_status(f"File generato: {txt_path}")
            messagebox.showinfo("Completato", f"File generato:\n{txt_path}")
        except Exception as exc:
            messagebox.showerror("Errore", f"Errore durante la conversione: {exc}")
            aggiorna_status(f"Errore: {exc}")

    tk.Button(container, text="Converti", command=converti).grid(
        row=3, column=0, columnspan=3, pady=10
    )

    container.columnconfigure(1, weight=1)
    container.rowconfigure(4, weight=1)

    root.mainloop()
