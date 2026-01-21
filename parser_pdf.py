import pdfplumber
import re


def estrai_dati_da_pdf(path):
    """
    Estrae i dati necessari al certificato stipendiale
    da un PDF cedolino strutturato (NON scansione).
    """

    dati = {
        "nominativo": "",
        "matricola": "",
        "cf": "",
        "periodo": "",
        "voci": [],
        "netto": None
    }

    with pdfplumber.open(path) as pdf:
        page = pdf.pages[0]

        # ==================================================
        # ESTRAZIONE PER COORDINATE – NOMINATIVO
        # area sotto linea tratteggiata, colonna sinistra
        # ==================================================
        words = page.extract_words(use_text_flow=True)

        nominativo_words = []

        for w in words:
            x0 = w["x0"]
            top = w["top"]
            text = w["text"]

            # sotto la linea tratteggiata
            if 90 < top < 140:
                # area sinistra (prima di Ruolo/Matricola)
                if x0 < 300:
                    nominativo_words.append((top, x0, text))

        # ordina per riga e colonna
        nominativo_words.sort()

        if nominativo_words:
            first_line_y = nominativo_words[0][0]
            nome_parts = [
                w[2] for w in nominativo_words
                if abs(w[0] - first_line_y) < 3
            ]
            dati["nominativo"] = " ".join(nome_parts)

        # ==================================================
        # TESTO COMPLETO (altri campi anagrafici)
        # ==================================================
        full_text = page.extract_text() or ""

        # --- MATRICOLA (area rossa a destra) ---
        m = re.search(r"Ruolo/Matricola\s+([^\n]+)", full_text)
        if m:
            dati["matricola"] = m.group(1).strip()

        # --- CODICE FISCALE ---
        m = re.search(r"Codice Fiscale\s+([A-Z0-9]{16})", full_text)
        if m:
            dati["cf"] = m.group(1)

        # --- PERIODO ---
        m = re.search(
            r"Retribuzione mese di\s+([A-Z]+\s+\d{4})",
            full_text,
            re.IGNORECASE
        )
        if m:
            dati["periodo"] = m.group(1)

        # ==================================================
        # PARSING VOCI ECONOMICHE PER COORDINATE
        # ==================================================
        COL_DESC_MAX = 320     # descrizione a sinistra
        COL_IMP_MIN = 360      # importi a destra

        righe = {}
        for w in words:
            y = round(w["top"], 1)
            righe.setdefault(y, []).append(w)

        for ws in righe.values():
            descrizione_parts = []
            importo = None

            for w in ws:
                x0 = w["x0"]
                testo = w["text"]

                # --- COLONNA DESCRIZIONE ---
                if x0 < COL_DESC_MAX:
                    descrizione_parts.append(testo)

                # --- COLONNA IMPORTI ---
                elif x0 > COL_IMP_MIN:
                    # scarta date (es. 14/05/1966)
                    if "/" in testo:
                        continue

                    # deve contenere decimali italiani
                    if "," not in testo:
                        continue

                    try:
                        importo = float(
                            testo.replace(".", "").replace(",", ".")
                        )
                    except ValueError:
                        continue

            if descrizione_parts and importo is not None:
                descrizione = " ".join(descrizione_parts).strip()

                dati["voci"].append({
                    "descrizione": descrizione,
                    "importo": importo
                })

                # intercetta netto a pagare
                if "Netto a pagare" in descrizione:
                    dati["netto"] = importo

    return dati
