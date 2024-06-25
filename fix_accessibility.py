import os
import logging
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTImage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import PDFPageAggregator

# Configure logging
log_file_path = 'log/accessibility_check.log'
logging.basicConfig(filename=log_file_path, level=logging.INFO, 
                    format='%(asctime)s %(levelname)s: %(message)s')

def check_tags(reader):
    """Check if the PDF has tags."""
    has_tags = '/MarkInfo' in reader.trailer['/Root']
    return has_tags

def check_images_alt_text(reader):
    """Check if images have alt text."""
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
    """Check if the PDF has metadata."""
    metadata = reader.metadata
    return metadata

def check_text_extraction(pdf_path):
    """Extract text and check if the PDF text is extractable."""
    text = extract_text(pdf_path)
    return bool(text.strip())

def check_logical_reading_order(pdf_path):
    """Check if the PDF has a logical reading order."""
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
    """Check if all fonts are embedded."""
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
    """Check if natural language is specified."""
    return 'Lang' in reader.trailer['/Root']

def check_structure_elements(reader):
    """Check for structure elements."""
    return '/StructTreeRoot' in reader.trailer['/Root']

def check_role_mapping(reader):
    """Check for role mapping."""
    if '/StructTreeRoot' in reader.trailer['/Root']:
        struct_tree_root = reader.trailer['/Root']['/StructTreeRoot']
        if '/RoleMap' in struct_tree_root:
            return True
    return False

def scan_pdf_for_accessibility(pdf_directory):
    """Scan all PDF files in the given directory for accessibility issues and log the results."""
    for filename in os.listdir(pdf_directory):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_directory, filename)
            try:
                reader = PdfReader(pdf_path)
                logging.info(f'Starting accessibility scan for {pdf_path}')
                
                has_tags = check_tags(reader)
                if has_tags:
                    logging.info(f'{pdf_path} has tags')
                else:
                    logging.warning(f'{pdf_path} does not have tags')

                alt_texts = check_images_alt_text(reader)
                for page, alts in alt_texts.items():
                    if alts:
                        logging.info(f'Page {page} of {pdf_path} has alt text for images')
                    else:
                        logging.warning(f'Page {page} of {pdf_path} does not have alt text for images')

                metadata = check_metadata(reader)
                if metadata:
                    logging.info(f'{pdf_path} has metadata: {metadata}')
                else:
                    logging.warning(f'{pdf_path} does not have metadata')

                text_extracted = check_text_extraction(pdf_path)
                if text_extracted:
                    logging.info(f'Text extraction successful for {pdf_path}')
                else:
                    logging.warning(f'Text extraction failed for {pdf_path}')

                logical_order = check_logical_reading_order(pdf_path)
                for page, order in logical_order.items():
                    if order:
                        logging.info(f'Page {page} of {pdf_path} has a logical reading order')
                    else:
                        logging.warning(f'Page {page} of {pdf_path} does not have a logical reading order')

                fonts_embedded = check_fonts_embedded(reader)
                for page, embedded in fonts_embedded.items():
                    if embedded:
                        logging.info(f'Page {page} of {pdf_path} has all fonts embedded')
                    else:
                        logging.warning(f'Page {page} of {pdf_path} does not have all fonts embedded')

                natural_language = check_natural_language(reader)
                if natural_language:
                    logging.info(f'{pdf_path} has a natural language specified')
                else:
                    logging.warning(f'{pdf_path} does not have a natural language specified')

                structure_elements = check_structure_elements(reader)
                if structure_elements:
                    logging.info(f'{pdf_path} has structure elements')
                else:
                    logging.warning(f'{pdf_path} does not have structure elements')

                role_mapping = check_role_mapping(reader)
                if role_mapping:
                    logging.info(f'{pdf_path} has role mapping')
                else:
                    logging.warning(f'{pdf_path} does not have role mapping')

                logging.info(f'Accessibility scan completed for {pdf_path}')
            except Exception as e:
                logging.error(f'Failed to process {pdf_path}: {e}')

if __name__ == "__main__":
    pdf_directory = 'src'
    scan_pdf_for_accessibility(pdf_directory)
    print(f"Accessibility scan completed. Check {log_file_path} for details.")
