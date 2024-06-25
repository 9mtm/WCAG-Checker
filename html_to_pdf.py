import os
import logging
import pdfkit

# Define paths
log_file_path = r'log/html_to_pdf.log'
fixed_html_directory = r'output/fixed_html'
final_pdf_directory = r'output/final_pdf'

# Configure the path to wkhtmltopdf
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

def ensure_directory_exists(directory):
    """Ensure the directory exists, if not, create it."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_log_file(log_file_path):
    """Clear the log file if it exists."""
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    with open(log_file_path, 'w') as file:
        pass

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(filename=log_file_path, level=logging.INFO, 
                        format='%(asctime)s %(levelname)s: %(message)s')

def html_to_pdf(html_path, pdf_path):
    """Convert HTML to PDF using pdfkit."""
    try:
        pdfkit.from_file(html_path, pdf_path, configuration=config)
        logging.info(f'Successfully converted {html_path} to {pdf_path}')
    except Exception as e:
        logging.error(f'Failed to convert {html_path} to PDF: {e}')

def convert_html_to_pdfs(fixed_html_directory, final_pdf_directory):
    """Convert all fixed HTML files to PDFs."""
    # Ensure required directories exist
    ensure_directory_exists(final_pdf_directory)
    ensure_directory_exists(os.path.dirname(log_file_path))

    # Clear previous log file
    clear_log_file(log_file_path)
    setup_logging()

    for filename in os.listdir(fixed_html_directory):
        if filename.endswith('.html'):
            html_path = os.path.join(fixed_html_directory, filename)
            pdf_path = os.path.join(final_pdf_directory, filename.replace('.html', '.pdf'))
            logging.info(f'Starting conversion of {html_path} to PDF')
            html_to_pdf(html_path, pdf_path)

    logging.info("All HTML files converted to PDF.")

# Convert fixed HTML files to PDFs
convert_html_to_pdfs(fixed_html_directory, final_pdf_directory)

logging.info("All HTML files converted to PDF.")
