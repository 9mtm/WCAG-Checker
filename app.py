import os
import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, Response
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams, LTTextBox, LTTextLine
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator

UPLOAD_FOLDER = 'src'
LOG_FOLDER = 'log'
LOG_FILE = os.path.join(LOG_FOLDER, 'accessibility_check.log')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LOG_FOLDER'] = LOG_FOLDER

def setup_logging():
    """Setup logging configuration with a rotating file handler."""
    log_handler = RotatingFileHandler(LOG_FILE, maxBytes=10240, backupCount=1)
    log_handler.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    log_handler.setFormatter(log_formatter)
    
    # Retry mechanism for log rollover
    original_doRollover = log_handler.doRollover
    def doRolloverWithRetry():
        for i in range(5):
            try:
                original_doRollover()
                break
            except PermissionError as e:
                if i < 4:
                    time.sleep(1)  # Wait for a second before retrying
                else:
                    raise e

    log_handler.doRollover = doRolloverWithRetry
    app.logger.addHandler(log_handler)

def ensure_directory_exists(directory):
    """Ensure the directory exists, if not, create it."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_log_file(log_file_path):
    """Clear the log file if it exists."""
    if os.path.exists(log_file_path):
        with open(log_file_path, 'w') as file:
            pass

def check_tags(reader):
    has_tags = '/MarkInfo' in reader.trailer['/Root']
    return has_tags

def check_images_alt_text(reader):
    alt_texts = {}
    for page_number, page in enumerate(reader.pages, start=1):
        alt_texts[page_number] = []
        if '/Annots' in page:
            for annot in page['/Annots']:
                annot_obj = annot.get_object()
                if annot_obj.get('/Subtype') == '/Link':
                    if '/A' in annot_obj and '/Alt' in annot_obj['/A']:
                        alt_texts[page_number].append(annot_obj['/A']['/Alt'])
    return alt_texts

def check_metadata(reader):
    metadata = reader.metadata
    return metadata

def check_xmp_metadata(reader):
    xmp_metadata = '/Metadata' in reader.trailer['/Root']
    return xmp_metadata

def check_pdf_ua_identifier(reader):
    pdf_ua_identifier = False
    if '/Metadata' in reader.trailer['/Root']:
        metadata = reader.trailer['/Root']['/Metadata']
        metadata_obj = metadata.get_object()
        if b'pdfuaid' in metadata_obj.get_data():
            pdf_ua_identifier = True
    return pdf_ua_identifier

def check_text_extraction(pdf_path):
    text = extract_text(pdf_path)
    return bool(text.strip())

def check_logical_reading_order(pdf_path):
    resource_manager = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(resource_manager, laparams=laparams)
    interpreter = PDFPageInterpreter(resource_manager, device)

    logical_order = {}
    with open(pdf_path, 'rb') as f:
        for page_number, page in enumerate(PDFPage.get_pages(f), start=1):
            interpreter.process_page(page)
            layout = device.get_result()
            logical_order[page_number] = True
            for element in layout:
                if isinstance(element, (LTTextBox, LTTextLine)):
                    if not element.get_text().strip():
                        logical_order[page_number] = False
                        break
    return logical_order

def check_fonts_embedded(reader):
    fonts_embedded = {}
    for page_number, page in enumerate(reader.pages, start=1):
        fonts_embedded[page_number] = True
        if '/Font' in page['/Resources']:
            for font in page['/Resources']['/Font'].values():
                font_obj = font.get_object()
                if '/FontFile' not in font_obj and '/FontFile2' not in font_obj and '/FontFile3' not in font_obj:
                    fonts_embedded[page_number] = False
    return fonts_embedded

def check_natural_language(reader):
    return 'Lang' in reader.trailer['/Root']

def check_structure_elements(reader):
    return '/StructTreeRoot' in reader.trailer['/Root']

def check_role_mapping(reader):
    if '/StructTreeRoot' in reader.trailer['/Root']:
        struct_tree_root = reader.trailer['/Root']['/StructTreeRoot']
        if '/RoleMap' in struct_tree_root:
            return True
    return False

def scan_pdf_for_accessibility(pdf_path):
    """Scan a PDF file for accessibility issues and log the results."""
    try:
        reader = PdfReader(pdf_path)
        app.logger.info(f'Starting accessibility scan for {pdf_path}')

        has_tags = check_tags(reader)
        if has_tags:
            app.logger.info(f'{pdf_path} has tags')
        else:
            app.logger.warning(f'{pdf_path} does not have tags')

        alt_texts = check_images_alt_text(reader)
        for page, alts in alt_texts.items():
            if alts:
                app.logger.info(f'Page {page} of {pdf_path} has alt text for images')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have alt text for images')

        metadata = check_metadata(reader)
        if metadata:
            app.logger.info(f'{pdf_path} has metadata: {metadata}')
        else:
            app.logger.warning(f'{pdf_path} does not have metadata')

        xmp_metadata = check_xmp_metadata(reader)
        if xmp_metadata:
            app.logger.info(f'{pdf_path} has XMP metadata')
        else:
            app.logger.warning(f'{pdf_path} does not have XMP metadata')

        pdf_ua_identifier = check_pdf_ua_identifier(reader)
        if pdf_ua_identifier:
            app.logger.info(f'{pdf_path} has PDF/UA identifier in XMP metadata')
        else:
            app.logger.warning(f'{pdf_path} does not have PDF/UA identifier in XMP metadata')

        text_extracted = check_text_extraction(pdf_path)
        if text_extracted:
            app.logger.info(f'Text extraction successful for {pdf_path}')
        else:
            app.logger.warning(f'Text extraction failed for {pdf_path}')

        logical_order = check_logical_reading_order(pdf_path)
        for page, order in logical_order.items():
            if order:
                app.logger.info(f'Page {page} of {pdf_path} has a logical reading order')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have a logical reading order')

        fonts_embedded = check_fonts_embedded(reader)
        for page, embedded in fonts_embedded.items():
            if embedded:
                app.logger.info(f'Page {page} of {pdf_path} has all fonts embedded')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have all fonts embedded')

        natural_language = check_natural_language(reader)
        if natural_language:
            app.logger.info(f'{pdf_path} has a natural language specified')
        else:
            app.logger.warning(f'{pdf_path} does not have a natural language specified')

        structure_elements = check_structure_elements(reader)
        if structure_elements:
            app.logger.info(f'{pdf_path} has structure elements')
        else:
            app.logger.warning(f'{pdf_path} does not have structure elements')

        role_mapping = check_role_mapping(reader)
        if role_mapping:
            app.logger.info(f'{pdf_path} has role mapping')
        else:
            app.logger.warning(f'{pdf_path} does not have role mapping')

        app.logger.info(f'Accessibility scan completed for {pdf_path}')
    except Exception as e:
        app.logger.error(f'Failed to process {pdf_path}: {e}')
        raise
    

@app.route('/')
def index():
    return render_template('homepage/index.html')

@app.route('/wcag-checklist')
def wcag_checklist():
    return render_template('homepage/sub-page/wcag-checklist.html')

@app.route('/color-contrast')
def color_contrast():
    return render_template('homepage/sub-page/color-contrast.html')

@app.route('/pdf-to-html')
def pdf_to_html():
    return render_template('homepage/sub-page/pdf-to-html.html')

@app.route('/fix-wcag')
def fix_wcag():
    return render_template('homepage/sub-page/fix-wcag.html')

@app.route('/scan-wcag-pdf')
def scan_wcag_pdf():
    return render_template('homepage/sub-page/scan-wcag-pdf.html')

@app.route('/scan-wcag-website')
def scan_wcag_website():
    return render_template('homepage/sub-page/scan-wcag-website.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            scan_pdf_for_accessibility(filepath)
            return redirect(url_for('show_results', filename=file.filename))
        return redirect(request.url)
    except Exception as e:
        app.logger.error(f'Error uploading file: {e}')
        return 'An error occurred while processing the file.', 500
    
@app.route('/results/<filename>')
def show_results(filename):
    try:
        with open(LOG_FILE, 'r') as log_file:
            log_content = log_file.readlines()
        
        warnings = sum(1 for line in log_content if "WARNING" in line)
        errors = sum(1 for line in log_content if "ERROR" in line)
        passed = len(log_content) - warnings - errors
        
        # Define a completion message
        if errors > 0 or warnings > 0:
            completion_message = "Scan completed with issues."
        else:
            completion_message = "Scan completed successfully with no issues."
        
        # Pass the completion message to the template
        return render_template('results.html', filename=filename, log_content=log_content, passed=passed, warnings=warnings, errors=errors, completion_message=completion_message)
    except Exception as e:
        app.logger.error(f'Error fetching log file for {filename}: {e}')
        return 'An error occurred while fetching the log file.', 500
    

@app.route('/log')
def download_log():
    return send_from_directory(app.config['LOG_FOLDER'], 'accessibility_check.log', as_attachment=True)

@app.route('/fetch_log')
def fetch_log():
    try:
        with open(LOG_FILE, 'r') as log_file:
            log_content = log_file.read()
        return Response(log_content, mimetype='text/plain')
    except Exception as e:
        app.logger.error(f'Error fetching log file: {e}')
        return Response('Error fetching log file', status=500, mimetype='text/plain')

if __name__ == '__main__':
    ensure_directory_exists(app.config['UPLOAD_FOLDER'])
    ensure_directory_exists(app.config['LOG_FOLDER'])
    clear_log_file(LOG_FILE)
    setup_logging()
    app.run(debug=True)


