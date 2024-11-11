
# imports
import sys
import logging
import json
from sitemap_parser import download_sitemaps, process_xml_file

# this file contains main script logic for downloading sitemaps, processing them, and writing scraped data to CSV

# Set up logging to log to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("job_scraper.log"),
        logging.StreamHandler(sys.stdout)  # Log to console as well
    ]
)


# Read variables from config.json

def read_config(config_file):
  with open(config_file, 'r') as f:
    config_data = json.load(f)
  return config_data

config_data = read_config('config.json')
sitemap_url = config_data['sitemap_url']
output_dir = config_data['output_dir']
output_csv = config_data['output_csv']
num_sitemaps = config_data['num_sitemaps']


def main(sitemap_url, output_dir, output_csv, num_sitemaps=5):
  """
  Downloads sitemaps, extracts job details, and saves them to a CSV file.

  Args:
      sitemap_url (str): URL of the sitemap index page from Monster.com.
      output_dir (str): Directory to save downloaded sitemap files.
      output_csv (str): Path to the output CSV file.
      num_sitemaps (int, optional): Number of sitemaps to download. Defaults to 5 for development stage.
  """

  # Download sitemaps
  downloaded_files = download_sitemaps(sitemap_url, output_dir, num_sitemaps)

  # Process each downloaded sitemap
  for sitemap_file in downloaded_files:
    process_xml_file(sitemap_file, output_csv)




# ---------------------
# ---Execution block---
# ---------------------

if __name__ == '__main__':
    main(sitemap_url, output_dir, output_csv)

    print(f"Finished scraping job details. Saved to: {output_csv}")
