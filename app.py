from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://stipendiuser:SY2gDbvYu3sMYROS4T1CDl533bniAXo7@dpg-d0k4ff56ubrc73av6avg-a/stipendidb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

class Progressivo(db.Model):
    __tablename__ = 'progressivi'
    id = db.Column(db.Integer, primary_key=True)
    nome_base = db.Column(db.String(50), nullable=False)
    anno = db.Column(db.Integer, nullable=False)
    progressivo = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('nome_base', 'anno', name='_nome_anno_uc'),)

def get_next_progressivo(nome_base):
    anno = datetime.now().year
    record = Progressivo.query.filter_by(nome_base=nome_base, anno=anno).first()
    if record:
        record.progressivo += 1
    else:
        record = Progressivo(nome_base=nome_base, anno=anno, progressivo=1)
        db.session.add(record)
    db.session.commit()
    return record.progressivo

def generate_filename():
    anno = datetime.now().year
    progressivo = get_next_progressivo('IRMEQS')
    return f"IRMEQS{anno}{progressivo:010}.TXT"

def format_record_rma(progressivo):
    identificativo_file = f"IRMEQS{datetime.now().year}{progressivo:010}"
    data_creazione = datetime.now().strftime('%Y%m%d')
    record = (
        'RMA' +                      # 001-003
        '0000001' +                  # 004-010
        identificativo_file.ljust(20)[:20] +  # 011-030
        data_creazione +            # 031-038
        'R01' +                     # 039-041
        ' ' * (300 - 41)            # 042-300
    )
    return record

def format_record_rmd(cod_fis, netto, index):
    tipo_record = 'RMD'
    progressivo_record = str(index + 2).zfill(7)   # 004-010 (inizia da 0000002)
    progressivo_richiesta = '0000001'
    tipo_soggetto = '1'
    codice_fiscale = cod_fis.ljust(16)[:16]

    oggi = datetime.now()
    identificativo_pagamento = f"FSHD{oggi.strftime('%Y%m%d')}{index + 2}".ljust(15)[:15]

    try:
        netto_float = float(netto.replace(',', '.'))
        importo = f"{int(netto_float * 100):015d}"
    except ValueError:
        importo = '0'.zfill(15)

    filler = ' ' * (300 - 64)

    return (
        tipo_record +
        progressivo_record +
        progressivo_richiesta +
        tipo_soggetto +
        codice_fiscale +
        identificativo_pagamento +
        importo +
        filler
    )

def format_record_rmz(count, progressivo):
    identificativo_file = f"IRMEQS{datetime.now().year}{progressivo:010}".ljust(20)[:20]
    data_creazione = datetime.now().strftime('%Y%m%d')
    progressivo_rmz = str(count + 2).zfill(7)  # RMA + RMD * N + RMZ = totale
    num_rmd = str(count).zfill(7)
    num_emf = '0000000'
    num_totale = str(count + 2).zfill(7)
    filler = ' ' * 71
    record = (
        'RMZ' +                   # 001-003
        progressivo_rmz +         # 004-010
        identificativo_file +     # 011-030
        data_creazione +          # 031-038
        num_rmd +                 # 039-045 (NUMERO RECORD EMD)
        num_emf +                 # 046-052 (NUMERO RECORD EMF)
        num_totale +              # 053-059 (TOTALE RECORD)
        filler                    # 060-130
    ).ljust(300)[:300]
    return record

def convert_csv_to_fixed_txt(csv_path, txt_path):
    progressivo = get_next_progressivo('IRMEQS')
    with open(csv_path, newline='', encoding='utf-8') as csvfile, open(txt_path, 'w', encoding='utf-8') as txtfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        rows = list(reader)

        # Record di testa RMA
        txtfile.write(format_record_rma(progressivo) + '\n')

        # Record di dettaglio RMD
        count = 0
        for i, row in enumerate(rows):
            cod_fis = row['COD_FIS'].strip()
            netto = row['NETTO'].strip()
            txtfile.write(format_record_rmd(cod_fis, netto, i) + '\n')
            count += 1

        # Record di coda RMZ
        txtfile.write(format_record_rmz(count, progressivo) + '\n')

def get_filename_by_progressivo(progressivo):
    anno = datetime.now().year
    return f"IRMEQS{anno}{progressivo:010}.TXT"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(csv_path)
            progressivo = get_next_progressivo('IRMEQS')
            filename = get_filename_by_progressivo(progressivo)
            txt_path = os.path.join(OUTPUT_FOLDER, filename)
            convert_csv_to_fixed_txt(csv_path, txt_path)
            return redirect(url_for('download', filename=filename))
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
