import os
import csv
from flask import Blueprint, request, render_template, send_file
from datetime import datetime
from calendar import monthrange

UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

hrsuite_bp = Blueprint('hrsuite', __name__, template_folder='templates')

@hrsuite_bp.route('/hrsuite', methods=['GET', 'POST'])
def hrsuite():
    result_filename = None
    if request.method == 'POST':
        # Upload dei file
        csv1 = request.files.get('csv_file_1')  # Anagrafico
        csv2 = request.files.get('csv_file_2')  # Compensi

        # Dati da form
        identificativoProvvedimento = request.form.get('identificativoProvvedimento', '').strip()
        anno = request.form.get('annoCompetenza')
        mese = request.form.get('meseCompetenza')
        codiceCapitolo = request.form.get('codiceCapitolo')
        codiceCentroDiCosto = request.form.get('codiceCentroDiCosto', '')
        riferimento = request.form.get('riferimento', '')
        nota = request.form.get('note', '')

        if csv1 and csv2 and csv1.filename.endswith('.CSV') and csv2.filename.endswith('.CSV'):
            path1 = os.path.join(UPLOAD_FOLDER, 'anagrafico.csv')
            path2 = os.path.join(UPLOAD_FOLDER, 'compensi.csv')
            csv1.save(path1)
            csv2.save(path2)

            result_filename = "output_hrsuite.csv"
            output_path = os.path.join(OUTPUT_FOLDER, result_filename)
            genera_output_hrsuite(
                path1, path2, output_path,
                identificativoProvvedimento,
                anno, mese,
                codiceCapitolo, codiceCentroDiCosto,
                riferimento, nota
            )

    return render_template('index.html', result_filename=result_filename)

@hrsuite_bp.route('/download_hrsuite/<filename>')
def download_hrsuite(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)

def genera_output_hrsuite(anagrafico_path, compensi_path, output_path,
                          identificativoProvvedimento, anno, mese,
                          codiceCapitolo, codiceCentroDiCosto,
                          riferimento, nota):
    
    # Costruzione dizionario da file anagrafico
    anagrafico = {}
    with open(anagrafico_path, newline='', encoding='utf-8') as a_file:
        reader = csv.DictReader(a_file, delimiter=';')
        for row in reader:
            nominativo = row.get("nominativo", "").strip().upper()
            anagrafico[nominativo] = {
                "matricola": row.get("matricola", "").zfill(6),
                "ruolo": row.get("ruolo", "ND")
            }

    # Data competenza voce calcolata
    try:
        anno_int = int(anno)
        mese_int = int(mese)
        last_day = monthrange(anno_int, mese_int)[1]
        dataCompetenzaVoce = f"{last_day:02d}/{mese_int:02d}/{anno_int}"
    except:
        dataCompetenzaVoce = ""

    # Intestazione finale
    intestazione = [
        "matricola", "comparto", "ruolo", "codiceVoce", "identificativoProvvedimento",
        "tipoProvvedimento", "numeroProvvedimento", "dataProvvedimento",
        "annoCompetenzaLiquidazione", "meseCompetenzaLiquidazione", "dataCompetenzaVoce",
        "codiceStatoVoce", "aliquota", "parti", "importo", "codiceDivisa",
        "codiceEnte", "codiceCapitolo", "codiceCentroDiCosto", "riferimento",
        "codiceRiferimentoVoce", "flagAdempimenti", "idContrattoCSA", "nota"
    ]

    # Apertura file compensi e creazione righe
    righe = []
    with open(compensi_path, newline='', encoding='utf-8') as c_file:
        reader = csv.DictReader(c_file, delimiter=';')
        for row in reader:
            nominativo = row.get("nominativo", "").strip().upper()
            if nominativo not in anagrafico:
                continue

            dati = anagrafico[nominativo]
            matricola = dati["matricola"]
            ruolo = dati["ruolo"]

            importo = row.get("importo", "").replace(".", "").replace(",", ".")
            try:
                importo_float = float(importo)
            except:
                importo_float = 0.0
            importo_str = f"{importo_float:.2f}".replace(".", ",")

            parti = row.get("parti", "").strip()
            parti = parti if parti else "1"

            riferimento_fmt = f"TL@{riferimento}@" if riferimento else ""

            tipoProvv = "" if identificativoProvvedimento else "029"
            numProvv = "" if identificativoProvvedimento else "61947"
            dataProvv = "" if identificativoProvvedimento else "09/05/2025"

            riga = [
                matricola, "1", ruolo, "04428", identificativoProvvedimento,
                tipoProvv, numProvv, dataProvv,
                anno, mese, dataCompetenzaVoce,
                "E", "0", parti, importo_str, "E",
                "000000", codiceCapitolo, codiceCentroDiCosto, riferimento_fmt,
                "", "", "", nota
            ]
            righe.append(riga)

    with open(output_path, 'w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out, delimiter=';')
        writer.writerow(intestazione)
        writer.writerows(righe)
