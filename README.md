# Convertitore CSV → TXT per Agenzia delle Entrate

Questa webapp Flask consente di:

- Caricare un file `.csv` con dati anagrafici e importi
- Generare un file `.TXT` a lunghezza fissa di 300 byte per record
- Includere 3 tipi di record nel file:
  - `RMA` – Record di testa
  - `RMD` – Record dettagliati (uno per ogni riga del CSV)
  - `RMZ` – Record di coda con totali e identificativo file

---

## 🧩 Formato del file TXT

Ogni riga è lunga esattamente 300 byte.

### 📌 RMA (Record di testa)

| Campo        | Posizione | Valore                       |
|--------------|-----------|------------------------------|
| Tipo record  | 001–003   | `RMA`                        |
| Progressivo  | 004–010   | `0000001`                    |
| Identificativo|011–030   | es. `IRMEQS20250000000001`   |
| Data         | 031–038   | formato `AAAAMMGG`           |
| Release      | 039–041   | `R01`                        |
| Filler       | 042–300   | Spazi                        |

---

### 📌 RMD (uno per ogni nominativo nel CSV)

| Campo                       | Posizione | Esempio                        |
|----------------------------|-----------|--------------------------------|
| Tipo record                | 001–003   | `RMD`                          |
| Progressivo record         | 004–010   | da `0000002` in poi            |
| Progressivo richiesta      | 011–017   | `0000001`                      |
| Tipo soggetto              | 018       | `1`                            |
| Codice fiscale             | 019–034   | da colonna `COD_FIS`           |
| Identificativo pagamento   | 035–049   | `FSHDAAAAMMGGNN`               |
| Importo del titolo         | 050–064   | 15 cifre, centesimi            |
| Filler                     | 065–300   | Spazi                          |

---

### 📌 RMZ (Record di coda)

| Campo                              | Posizione | Valore                              |
|-----------------------------------|-----------|-------------------------------------|
| Tipo record                       | 001–003   | `RMZ`                               |
| Progressivo finale                | 004–010   | ultimo record + 1                   |
| Identificativo file               | 011–030   | come `RMA`                          |
| Data creazione                    | 031–038   | formato `AAAAMMGG`                  |
| Totale record `RMD` (EMD)         | 039–045   | es. `0000010`                       |
| Totale record `EMF`               | 046–052   | `0000000`                           |
| Totale record (RMA+RMD+RMZ)       | 053–059   | es. `0000012`                       |
| Filler                            | 060–130   | Spazi                               |

---

## 🧑‍💻 Requisiti

- Python 3.8+
- PostgreSQL (Render o locale)
- Dipendenze Python:
