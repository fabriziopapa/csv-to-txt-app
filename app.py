from flask import Flask, render_template, request, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/dbname')
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

def get_next_progressivo(nome_base='dichiarazione'):
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
    base = 'dichiarazione'
    anno = datetime.now().year
    progressivo = get_next_progressivo(base)
    return f"{base}_{anno}_{progressivo:03}.txt"

def convert_csv_to_fixed_txt(csv_path, txt_path):
    with open(csv_path, newline='') as csvfile, open(txt_path, 'w') as txtfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            line = ''.join(row).ljust(300)[:300]  # riga a lunghezza fissa
            txtfile.write(line + '\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if file and file.filename.endswith('.csv'):
            csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(csv_path)
            filename = generate_filename()
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
