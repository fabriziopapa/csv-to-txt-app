from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import csv
import traceback
from hrsuite import hrsuite_bp 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.register_blueprint(hrsuite_bp)
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

# Rotta manuale per creare la tabella su Render
@app.route('/initdb')
def initdb():
    try:
        with app.app_context():
            db.create_all()
        return "Tabelle create correttamente."
    except Exception as e:
        return f"Errore nella creazione delle tabelle: {str(e)}"
# Informazioni di versione da Git (se disponibili)
def get_git_info():
    try:
        commit = os.popen("git log -1 --pretty=%s").read().strip()
        date = os.popen("git log -1 --format=%cd --date=short").read().strip()
        return commit, date
    except Exception as e:
        return "Versione sconosciuta", "Data sconosciuta"

@app.context_processor
def inject_git_info():
    commit, date = get_git_info()
    return dict(git_commit=commit, 
                git_date=date,
                app_notice="Applicazione locale - nessun dato sensibile o fiscale viene memorizzato in remoto"
                )

@app.route('/info')
def info():
    return {
        "versione": get_git_info()[0],
        "data_push": get_git_info()[1]
    }

@app.route('/alert')
def alert():
    return "Applicazione locale - nessun dato sensibile o fiscale viene memorizzato in remoto"
    
def get_next_progressivo(nome_base, commit=True):
    anno = datetime.now().year
    print(f"Recupero progressivo per {nome_base} - anno {anno}")
    record = Progressivo.query.filter_by(nome_base=nome_base, anno=anno).first()
    if record:
        record.progressivo += 1
        print(f"Progressivo esistente trovato: nuovo progressivo = {record.progressivo}")
    else:
        record = Progressivo(nome_base=nome_base, anno=anno, progressivo=1)
        db.session.add(record)
        print("Creato nuovo record progressivo = 1")
    if commit:
        db.session.commit()
    return record.progressivo

def generate_filename():
    anno = datetime.now().year
    progressivo = get_next_progressivo('IRMEQS')
    filename = f"IRMEQS{anno}{progressivo:010}.TXT"
    print(f"Generato nome file: {filename}")
    return filename

def format_record_rma(progressivo):
    identificativo_file = f"IRMEQS{datetime.now().year}{progressivo:010}"
    data_creazione = datetime.now().strftime('%Y%m%d')
    print(f"Creazione RMA: identificativo_file={identificativo_file}, data={data_creazione}")
    record = (
        'RMA' +
        '0000001' +
        identificativo_file.ljust(20)[:20] +
        data_creazione +
        'R01' +
        ' ' * (300 - 41)
    )
    return record

def format_record_rmd(cod_fis, netto, index):
    print(f"Creazione RMD {index + 2}: CF={cod_fis}, netto={netto}")
    tipo_record = 'RMD'
    progressivo_record = str(index + 2).zfill(7)
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
        print("Valore netto non valido, impostato a 0")
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
    progressivo_rmz = str(count + 2).zfill(7)
    num_rmd = str(count+2).zfill(7)
    #num_emf = '0000000'
    #num_totale = str(count + 2).zfill(7)
    filler = ' ' * 85
    #print(f"Creazione RMZ: progressivo={progressivo_rmz}, totale RMD={num_rmd}, totale={num_totale}")
    print(f"Creazione RMZ: progressivo={progressivo_rmz}, totale RMD={num_rmd}")
    record = (
        'RMZ' +
        progressivo_rmz +
        identificativo_file +
        data_creazione +
        num_rmd +
        #num_emf +
        #num_totale +
        filler
    ).ljust(300)[:300]
    return record

def convert_csv_to_fixed_txt(csv_path, txt_path, progressivo):
    print(f"Apro CSV da: {csv_path} e scrivo TXT in: {txt_path}")
    with open(csv_path, newline='', encoding='utf-8',errors='replace') as csvfile, open(txt_path, 'w', encoding='utf-8') as txtfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        rows = list(reader)
        txtfile.write(format_record_rma(progressivo) + '\n')
        count = 0
        for i, row in enumerate(rows):
            cod_fis = row['COD_FIS'].strip()
            netto = row['NETTO'].strip()
            if not cod_fis:
                raise ValueError(f"COD_FIS mancante alla riga {i+2} del CSV")  # +2 perché header + 1-based
            
            txtfile.write(format_record_rmd(cod_fis, netto, i) + '\n')
            count += 1
        txtfile.write(format_record_rmz(count, progressivo) + '\n')
        print(f"File TXT generato con {count} record RMD")

def get_filename_by_progressivo(progressivo):
    anno = datetime.now().year
    return f"IRMEQS{anno}{progressivo:010}.TXT"

@app.route('/', methods=['GET', 'POST'])
def index():
    filename = None
    error_message = None  # ← inizializza qui
    if request.method == 'POST':
        print("Ricevuta richiesta POST con file CSV")
        file = request.files.get('csv_file')
        if file and file.filename.lower().endswith('.csv'):
            print(f"File valido ricevuto: {file.filename}")
            csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
            try:
                file.save(csv_path)
                progressivo = get_next_progressivo('IRMEQS', commit=False)  # modifica la funzione per supportare commit=False
                filename = get_filename_by_progressivo(progressivo)
                txt_path = os.path.join(OUTPUT_FOLDER, filename)
                convert_csv_to_fixed_txt(csv_path, txt_path, progressivo)
                get_next_progressivo('IRMEQS', commit=True)  # conferma l'incremento
            except Exception as e:
                print("Errore durante la elaborazione CSV:", e)
                traceback.print_exc()
                error_message = str(e)
                filename = None

        else:
            error_message = "File non valido o assente. Carica un CSV."
    return render_template('index.html', filename=filename,error_message=error_message)

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    print(f"Download richiesto per: {filename}")
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Applicazione Flask avviata in modalità debug")
    app.run(debug=True)
