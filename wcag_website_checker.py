import requests
from bs4 import BeautifulSoup
from wcag_zoo.validators import HTMLValidator

def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch the URL: {url}")

def check_accessibility(html_content):
    validator = HTMLValidator()
    results = validator.validate(html_content)
    return results

def print_results(results):
    for result in results:
        print(f"Guideline: {result.guideline}")
        print(f"Level: {result.level}")
        print(f"Message: {result.message}")
        print(f"Element: {result.element}\n")

if __name__ == "__main__":
    url = input("Enter the URL of the website to check: ")
    try:
        html_content = fetch_html(url)
        results = check_accessibility(html_content)
        print_results(results)
    except Exception as e:
        print(str(e))
