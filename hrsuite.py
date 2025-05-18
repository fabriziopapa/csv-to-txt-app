# hrsuite.py
import os
import csv
from flask import Blueprint, request, render_template, send_file

UPLOAD_FOLDER = '/tmp/uploads'
OUTPUT_FOLDER = '/tmp/outputs'

hrsuite_bp = Blueprint('hrsuite', __name__, template_folder='templates')

@hrsuite_bp.route('/hrsuite', methods=['GET', 'POST'])
def hrsuite():
    result_filename = None
    if request.method == 'POST':
        csv1 = request.files.get('csv_file_1')
        csv2 = request.files.get('csv_file_2')
        if csv1 and csv2 and csv1.filename.endswith('.CSV') and csv2.filename.endswith('.CSV'):
            path1 = os.path.join(UPLOAD_FOLDER, 'modulo1.csv')
            path2 = os.path.join(UPLOAD_FOLDER, 'modulo2.csv')
            csv1.save(path1)
            csv2.save(path2)

            # TODO: Inserire logica di elaborazione CSV qui
            result_filename = "output_hrsuite.csv"
            output_path = os.path.join(OUTPUT_FOLDER, result_filename)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['ESEMPIO_CAMPO_1', 'ESEMPIO_CAMPO_2'])
                writer.writerow(['DATO1', 'DATO2'])

    return render_template('index.html', result_filename=result_filename)

@hrsuite_bp.route('/download_hrsuite/<filename>')
def download_hrsuite(filename):
    path = os.path.join(OUTPUT_FOLDER, filename)
    return send_file(path, as_attachment=True)
