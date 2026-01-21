from flask import Blueprint, render_template, request

from parser_pdf import estrai_dati_da_pdf

pdf_parser_bp = Blueprint("pdf_parser", __name__, template_folder="templates")


@pdf_parser_bp.route("/pdf-parser", methods=["GET", "POST"])
def pdf_parser():
    pdf_data = None
    pdf_error_message = None

    if request.method == "POST":
        file = request.files.get("pdf_file")
        if file and file.filename.lower().endswith(".pdf"):
            try:
                pdf_data = estrai_dati_da_pdf(file.stream)
            except Exception as exc:
                pdf_error_message = f"Errore durante la lettura del PDF: {exc}"
        else:
            pdf_error_message = "File non valido o assente. Carica un PDF."

    return render_template(
        "index.html",
        pdf_data=pdf_data,
        pdf_error_message=pdf_error_message,
        active_section="pdf-parser",
    )
