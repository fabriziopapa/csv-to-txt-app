# CSV to Fixed-Length TXT Converter

Una semplice webapp in Flask che consente di:

- Caricare un file CSV (separato da `;`)
- Convertirlo in un file `.TXT` con **righe a lunghezza fissa di 300 byte**
- Generare un nome file univoco secondo lo schema:  
  `dichiarazione_<anno>_<progressivo>.txt`
- Scaricare il file .TXT elaborato

## 📦 Funzionalità

- Interfaccia web single-page
- Upload sicuro dei file CSV
- Generazione progressiva del nome file tramite database PostgreSQL
- Supporto a Render.com per deploy automatico

## 🛠 Requisiti

- Python 3.8+
- PostgreSQL (locale o su Render)
- Dipendenze:
