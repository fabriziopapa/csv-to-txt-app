from datetime import datetime
import csv


def format_record_rma(progressivo):
    identificativo_file = f"IRMEQS{datetime.now().year}{progressivo:010}"
    data_creazione = datetime.now().strftime("%Y%m%d")
    record = (
        "RMA"
        + "0000001"
        + identificativo_file.ljust(20)[:20]
        + data_creazione
        + "R01"
        + " " * (300 - 41)
    )
    return record


def format_record_rmd(cod_fis, netto, index):
    tipo_record = "RMD"
    progressivo_record = str(index + 2).zfill(7)
    progressivo_richiesta = "0000001"
    tipo_soggetto = "1"
    codice_fiscale = cod_fis.ljust(16)[:16]
    oggi = datetime.now()
    identificativo_pagamento = f"FSHD{oggi.strftime('%Y%m%d')}{index + 2}".ljust(15)[:15]
    try:
        netto_float = float(netto.replace(",", "."))
        importo = f"{int(netto_float * 100):015d}"
    except ValueError:
        importo = "0".zfill(15)
    flag_pos65 = "1"  # posizione 65
    filler = " " * (300 - 65)
    return (
        tipo_record
        + progressivo_record
        + progressivo_richiesta
        + tipo_soggetto
        + codice_fiscale
        + identificativo_pagamento
        + importo
        + flag_pos65
        + filler
    )


def format_record_rmz(count, progressivo):
    identificativo_file = f"IRMEQS{datetime.now().year}{progressivo:010}".ljust(20)[:20]
    data_creazione = datetime.now().strftime("%Y%m%d")
    progressivo_rmz = str(count + 2).zfill(7)
    num_rmd = str(count + 2).zfill(7)
    filler = " " * 85
    record = (
        "RMZ"
        + progressivo_rmz
        + identificativo_file
        + data_creazione
        + num_rmd
        + filler
    ).ljust(300)[:300]
    return record


def convert_csv_to_fixed_txt(csv_path, txt_path, progressivo):
    with open(
        csv_path, newline="", encoding="utf-8", errors="replace"
    ) as csvfile, open(txt_path, "w", encoding="utf-8") as txtfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        rows = list(reader)
        txtfile.write(format_record_rma(progressivo) + "\n")
        count = 0
        for i, row in enumerate(rows):
            cod_fis = row["COD_FIS"].strip()
            netto = row["NETTO"].strip()
            if not cod_fis:
                raise ValueError(
                    f"COD_FIS mancante alla riga {i + 2} del CSV"
                )  # +2 perché header + 1-based

            txtfile.write(format_record_rmd(cod_fis, netto, i) + "\n")
            count += 1
        txtfile.write(format_record_rmz(count, progressivo) + "\n")
