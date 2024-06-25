import os
import time
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify, render_template
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
    results = {}
    try:
        reader = PdfReader(pdf_path)
        app.logger.info(f'Starting accessibility scan for {pdf_path}')

        has_tags = check_tags(reader)
        results['tags'] = has_tags
        if has_tags:
            app.logger.info(f'{pdf_path} has tags')
        else:
            app.logger.warning(f'{pdf_path} does not have tags')

        alt_texts = check_images_alt_text(reader)
        results['alt_texts'] = alt_texts
        for page, alts in alt_texts.items():
            if alts:
                app.logger.info(f'Page {page} of {pdf_path} has alt text for images')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have alt text for images')

        metadata = check_metadata(reader)
        results['metadata'] = metadata
        if metadata:
            app.logger.info(f'{pdf_path} has metadata: {metadata}')
        else:
            app.logger.warning(f'{pdf_path} does not have metadata')

        xmp_metadata = check_xmp_metadata(reader)
        results['xmp_metadata'] = xmp_metadata
        if xmp_metadata:
            app.logger.info(f'{pdf_path} has XMP metadata')
        else:
            app.logger.warning(f'{pdf_path} does not have XMP metadata')

        pdf_ua_identifier = check_pdf_ua_identifier(reader)
        results['pdf_ua_identifier'] = pdf_ua_identifier
        if pdf_ua_identifier:
            app.logger.info(f'{pdf_path} has PDF/UA identifier in XMP metadata')
        else:
            app.logger.warning(f'{pdf_path} does not have PDF/UA identifier in XMP metadata')

        text_extracted = check_text_extraction(pdf_path)
        results['text_extracted'] = text_extracted
        if text_extracted:
            app.logger.info(f'Text extraction successful for {pdf_path}')
        else:
            app.logger.warning(f'Text extraction failed for {pdf_path}')

        logical_order = check_logical_reading_order(pdf_path)
        results['logical_order'] = logical_order
        for page, order in logical_order.items():
            if order:
                app.logger.info(f'Page {page} of {pdf_path} has a logical reading order')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have a logical reading order')

        fonts_embedded = check_fonts_embedded(reader)
        results['fonts_embedded'] = fonts_embedded
        for page, embedded in fonts_embedded.items():
            if embedded:
                app.logger.info(f'Page {page} of {pdf_path} has all fonts embedded')
            else:
                app.logger.warning(f'Page {page} of {pdf_path} does not have all fonts embedded')

        natural_language = check_natural_language(reader)
        results['natural_language'] = natural_language
        if natural_language:
            app.logger.info(f'{pdf_path} has a natural language specified')
        else:
            app.logger.warning(f'{pdf_path} does not have a natural language specified')

        structure_elements = check_structure_elements(reader)
        results['structure_elements'] = structure_elements
        if structure_elements:
            app.logger.info(f'{pdf_path} has structure elements')
        else:
            app.logger.warning(f'{pdf_path} does not have structure elements')

        role_mapping = check_role_mapping(reader)
        results['role_mapping'] = role_mapping
        if role_mapping:
            app.logger.info(f'{pdf_path} has role mapping')
        else:
            app.logger.warning(f'{pdf_path} does not have role mapping')

        app.logger.info(f'Accessibility scan completed for {pdf_path}')
    except Exception as e:
        app.logger.error(f'Error scanning {pdf_path}: {e}')
        results['error'] = str(e)
    
    return results

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file:
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            results = scan_pdf_for_accessibility(file_path)
            return jsonify(results)
    return render_template('index.html')

if __name__ == '__main__':
    ensure_directory_exists(UPLOAD_FOLDER)
    ensure_directory_exists(LOG_FOLDER)
    clear_log_file(LOG_FILE)
    setup_logging()
    app.run(debug=True)
