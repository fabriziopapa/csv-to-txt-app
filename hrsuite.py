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
        print("\n[DEBUG] --- HRSuite POST ricevuto ---")
        # Upload dei file
        csv1 = request.files.get('csv_file_1')  # Anagrafico
        csv2 = request.files.get('csv_file_2')  # Compensi

        # Dati da form
        identificativoProvvedimento = request.form.get('identificativoProvvedimento', '').strip()
        anno = request.form.get('annoCompetenza')
        mese = request.form.get('meseCompetenza')
        codiceVoce = request.form.get('codiceVoce')
        codiceCapitolo = request.form.get('codiceCapitolo')
        codiceCentroDiCosto = request.form.get('codiceCentroDiCosto', '')
        riferimento = request.form.get('riferimento', '')
        nota = request.form.get('note', '')
        # Flag “Compensi omnicomprensivi”
        compensi_omnicomprensivi = request.form.get('compensi_omnicomprensivi') == 'on'
        print(f"[DEBUG] Compensi omnicomprensivi: {compensi_omnicomprensivi}")


        print(f"[DEBUG] Form values → identificativoProvv: '{identificativoProvvedimento}', "
              f"anno: {anno}, mese: {mese}, codiceVoce: {codiceVoce}, codiceCapitolo: {codiceCapitolo}, "
              f"codiceCentroDiCosto: '{codiceCentroDiCosto}', riferimento: '{riferimento}', nota: '{nota}'")

        if not (csv1 and csv2 and csv1.filename.endswith('.CSV') and csv2.filename.endswith('.CSV')):
            print("[DEBUG] File CSV mancanti o con estensione errata.")
        else:
            path1 = os.path.join(UPLOAD_FOLDER, 'anagrafico.csv')
            path2 = os.path.join(UPLOAD_FOLDER, 'compensi.csv')
            csv1.save(path1)
            csv2.save(path2)
            print(f"[DEBUG] File salvati → anagrafico: {path1}, compensi: {path2}")

            result_filename = "output_hrsuite.csv"
            output_path = os.path.join(OUTPUT_FOLDER, result_filename)
            genera_output_hrsuite(
                path1, path2, output_path,
                identificativoProvvedimento,
                anno, mese,
                codiceVoce, codiceCapitolo, codiceCentroDiCosto,
                riferimento, nota
            )
            print(f"[DEBUG] Generato file: {output_path}")

    return render_template('index.html', result_filename=result_filename)

@hrsuite_bp.route('/download_hrsuite/<filename>')
def download_hrsuite(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    print(f"[DEBUG] Download richiesto per: {path}")
    return send_file(path, as_attachment=True)

def genera_output_hrsuite(anagrafico_path, compensi_path, output_path,
                          identificativoProvvedimento,
                          anno, mese,
                          codiceVoce, codiceCapitolo, codiceCentroDiCosto,
                          riferimento, nota,compensi_omnicomprensivi):

    print("\n[DEBUG] --- Inizio genera_output_hrsuite ---")
    print(f"[DEBUG] Paths in input → anagrafico: {anagrafico_path}, compensi: {compensi_path}")
    print(f"[DEBUG] Output → {output_path}")

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
        print(f"[DEBUG] Lettura anagrafico: {len(anagrafico)} voci caricate")

    # Calcolo dataCompetenzaVoce
    try:
        anno_int = int(anno)
        mese_int = int(mese)
        last_day = monthrange(anno_int, mese_int)[1]
        dataCompetenzaVoce = f"{last_day:02d}/{mese_int:02d}/{anno_int}"
    except Exception as e:
        dataCompetenzaVoce = ""
        print(f"[DEBUG] Errore calcolo dataCompetenzaVoce: {e}")

    # Intestazione finale
    intestazione = [
        "matricola", "comparto", "ruolo", "codiceVoce", "identificativoProvvedimento",
        "tipoProvvedimento", "numeroProvvedimento", "dataProvvedimento",
        "annoCompetenzaLiquidazione", "meseCompetenzaLiquidazione", "dataCompetenzaVoce",
        "codiceStatoVoce", "aliquota", "parti", "importo", "codiceDivisa",
        "codiceEnte", "codiceCapitolo", "codiceCentroDiCosto", "riferimento",
        "codiceRiferimentoVoce", "flagAdempimenti", "idContrattoCSA", "nota"
    ]

    righe = []
    mancanti = 0
    with open(compensi_path, newline='', encoding='utf-8') as c_file:
        reader = csv.DictReader(c_file, delimiter=';')
        for i, row in enumerate(reader, start=1):
            nominativo = row.get("nominativo", "").strip().upper()
            if nominativo not in anagrafico:
                print(f"[DEBUG] RIGA {i}: nominativo '{nominativo}' NON trovato in anagrafico")
                mancanti += 1
                continue

            dati = anagrafico[nominativo]
            matricola = dati["matricola"]
            ruolo = dati["ruolo"]

            importo_raw = row.get("importo", "").strip()
            parti_raw = row.get("parti", "").strip()
            print(f"[DEBUG] RIGA {i}: nominativo '{nominativo}', importo='{importo_raw}', parti='{parti_raw}'")

            # importo
            try:
                imp = float(importo_raw.replace(".", "").replace(",", ".")) if importo_raw else 0.0
                if compensi_omnicomprensivi:
                    # flag ON → applica scorporo
                    if ruolo == "RD":
                        imp = imp / (1 + 0.3431)
                    else:
                        imp = imp / (1 + 0.3270)
                # else (flag OFF) → imp rimane raw_importo
            except:
                imp = 0.0
                print(f"[DEBUG] RIGA {i}: importo non valido → '{importo_raw}', imposto 0")
            importo_str = f"{imp:.2f}".replace(".", ",")

            parti = parti_raw if parti_raw else "1"

            riferimento_fmt = f"TL@{riferimento}@" if riferimento else ""

            # Provvedimento
            tipoProvv = "" if identificativoProvvedimento else "029"
            numProvv = "" if identificativoProvvedimento else "61947"
            dataProvv = "" if identificativoProvvedimento else "09/05/2025"

            riga = [
                matricola, "1", ruolo, codiceVoce, identificativoProvvedimento,
                tipoProvv, numProvv, dataProvv,
                anno, mese, dataCompetenzaVoce,
                "E", "0", parti, importo_str, "E",
                "000000", codiceCapitolo, codiceCentroDiCosto, riferimento_fmt,
                "", "", "", nota
            ]
            righe.append(riga)

        print(f"[DEBUG] Compensi processati: {i} righe, {len(righe)} generate, {mancanti} mancanti")

    # Scrittura output
    with open(output_path, 'w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out, delimiter=';')
        writer.writerow(intestazione)
        writer.writerows(righe)
        print(f"[DEBUG] File '{output_path}' scritto con {len(righe)} record.")
    print("[DEBUG] --- Fine genera_output_hrsuite ---\n")
