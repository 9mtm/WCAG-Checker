import os
import logging
import subprocess
import shutil
from fix_accessibility import fix_html_file

# Define paths
log_file_path = r'log/accessibility_fixes.log'
pdf_directory = r'src'
html_directory = r'output/temp_html'
fixed_html_directory = r'output/fixed_html'

def ensure_directory_exists(directory):
    """Ensure the directory exists, if not, create it."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def clear_directory(directory):
    """Clear all files in the given directory."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

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

def pdf_to_html(pdf_path, html_dir):
    """Convert PDF to HTML using pdf2htmlEX."""
    ensure_directory_exists(html_dir)
    html_path = os.path.join(html_dir, os.path.basename(pdf_path).replace('.pdf', '.html'))
    command = f'"C:\\Users\\malarade\\developer\\py\\pdf2htmlEX\\pdf2htmlEX.exe" --dest-dir "{html_dir}" "{pdf_path}"'
    try:
        logging.info(f'Converting {pdf_path} to HTML')
        subprocess.run(command, shell=True, check=True)
        logging.info(f'Successfully converted {pdf_path} to {html_path}')
    except subprocess.CalledProcessError as e:
        logging.error(f'Failed to convert {pdf_path} to HTML: {e}')
    return html_path

def process_html_files(html_directory, fixed_html_directory):
    """Process HTML files to fix accessibility issues."""
    # Ensure required directories exist
    ensure_directory_exists(fixed_html_directory)
    ensure_directory_exists(os.path.dirname(log_file_path))

    total_issues_fixed = 0
    total_issues_remaining = 0

    for filename in os.listdir(html_directory):
        if filename.endswith('.html'):
            file_path = os.path.join(html_directory, filename)
            fixed_file_path = os.path.join(fixed_html_directory, filename)
            title = os.path.basename(filename).replace('.html', '')
            try:
                logging.info(f'Starting processing of {file_path}')
                issues_fixed = fix_html_file(file_path, fixed_file_path, title)
                total_issues_fixed += issues_fixed
                logging.info(f'Finished processing of {file_path} with {issues_fixed} issues fixed.')
            except Exception as e:
                logging.error(f'Failed to process {file_path}: {e}')
                total_issues_remaining += 1
    
    logging.info(f'Total issues fixed across all files: {total_issues_fixed}')
    logging.info(f'Total issues remaining across all files: {total_issues_remaining}')

def convert_and_process_pdfs(pdf_directory, html_directory, fixed_html_directory):
    """Convert PDFs to HTML and then process the HTML files for accessibility."""
    # Clear previous files and log file
    clear_directory(html_directory)
    clear_directory(fixed_html_directory)
    clear_log_file(log_file_path)
    setup_logging()

    for filename in os.listdir(pdf_directory):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(pdf_directory, filename)
            html_path = pdf_to_html(pdf_path, html_directory)
            if os.path.exists(html_path):
                title = os.path.basename(filename).replace('.pdf', '')
                logging.info(f'Starting processing of {html_path}')
                issues_fixed = fix_html_file(html_path, os.path.join(fixed_html_directory, os.path.basename(html_path)), title)
                logging.info(f'Finished processing of {html_path} with {issues_fixed} issues fixed.')

    logging.info("All files processed.")

# Convert PDFs to HTML and process the HTML files
convert_and_process_pdfs(pdf_directory, html_directory, fixed_html_directory)

logging.info("All files processed.")
