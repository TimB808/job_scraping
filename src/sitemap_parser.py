
# imports
import csv
import requests
import logging
import time
from scraper import process_job_url
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import random
from fake_useragent import UserAgent
from validators import url as validate_url
import os
import gzip


# This file contains functions to download sitemap files, parse them for URLs, and save scraped details to csv file,

# define functions to go through the URLs in xml.gz file, scraping elements from each URL and saving in csv file

def prepare_files(xml_gz_file, output_csv):
    """Prepare absolute paths and open output CSV file."""
    xml_gz_file = os.path.abspath(xml_gz_file)
    output_csv = os.path.abspath(output_csv)
    return xml_gz_file, output_csv

def parse_xml_and_filter_urls(xml_gz_file, namespace, cutoff_date, max_urls=10):
    """Parse XML file, filter URLs by date, and yield valid URLs."""
    with gzip.open(xml_gz_file, 'rt', encoding='utf-8') as f:
        tree = ET.parse(f)
        root = tree.getroot()
        processed_urls = 0

        for url_elem in root.findall('ns:url', namespace):
            if processed_urls >= max_urls:
                break
            loc_elem = url_elem.find('ns:loc', namespace)
            lastmod_elem = url_elem.find('ns:lastmod', namespace)

            if loc_elem is not None and lastmod_elem is not None:
                url = loc_elem.text

                if not validate_url(url):  # Skips invalid URLs
                    logging.warning(f"Invalid URL format: {url}")
                    continue

                try:
                    lastmod_date = datetime.strptime(lastmod_elem.text[:10], '%Y-%m-%d').date()
                except ValueError:
                    logging.warning(f"Skipping URL due to invalid date format: {url}")
                    continue

                if lastmod_date < cutoff_date or 'sitemaps' in url:
                    continue  # Skip outdated or irrelevant URLs

                processed_urls += 1
                yield url




# Define function to download XML.gz files (sitemaps) from Monster.com page including rotating headers and random sleep delay).
def download_sitemaps(sitemap_url, output_dir, num_sitemaps=5):
    """Download XML sitemap files from a sitemap index page and return a list of downloaded file paths."""

    ua = UserAgent()  # Create an instance of UserAgent
    headers = {
        'User-Agent': ua.random,  # Use a random User-Agent
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/xml;q=0.9,text/html;q=0.8,*/*;q=0.7',
    }

    # Initial request to get the sitemap index
    response = requests.get(sitemap_url, headers=headers)
    response.raise_for_status()  # Ensure the request was successful

    sitemap_root = ET.fromstring(response.content)
    ns = {'ns': "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Retrieve URLs with validation
    sitemap_urls = []
    for loc in sitemap_root.findall('ns:sitemap/ns:loc', ns)[:num_sitemaps]:
        sitemap_loc = loc.text
        if validate_url(sitemap_loc):  # Validate each sitemap URL
            sitemap_urls.append(sitemap_loc)
        else:
            logging.warning(f"Skipping invalid sitemap URL: {sitemap_loc}")

    downloaded_files = []  # To store paths of downloaded files

    for index, sitemap_url in enumerate(sitemap_urls, start=1):
        try:
            logging.info(f"Downloading sitemap {index}: {sitemap_url}")
            sitemap_response = requests.get(sitemap_url, headers=headers)
            sitemap_response.raise_for_status()

            # Save each XML.gz file in the output directory
            file_name = os.path.join(output_dir, f"sitemap_{index}.xml.gz")
            with open(file_name, 'wb') as f:
                f.write(sitemap_response.content)

            downloaded_files.append(file_name)  # Append path to the list
            logging.info(f"Saved sitemap {index} to {file_name}")

            # Random delay between requests
            time.sleep(random.uniform(3, 7))  # Random delay between 3 to 7 seconds

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download {sitemap_url}. Error: {e}")

    return downloaded_files  # Return the list of downloaded file paths


def write_to_csv(output_csv, fieldnames, job_details):
    """Write job details to CSV file."""
    with open(output_csv, mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        if csv_file.tell() == 0:
            writer.writeheader()  # Write header if file is empty
        writer.writerow({
            'Job Title': job_details.get('job_title', 'None'),
            'Employer': job_details.get('employer', 'None'),
            'Salary': job_details.get('salary', 'None'),
            'Description': job_details.get('description', 'None'),
            'Requirements': job_details.get('requirements', 'None')
        })

def process_xml_file(xml_gz_file, output_csv, num_urls=10):
    """Main function to process XML file and extract job data."""
    xml_gz_file, output_csv = prepare_files(xml_gz_file, output_csv)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    today = datetime.now().date()
    cutoff_date = today - timedelta(weeks=1)
    fieldnames = ['Job Title', 'Employer', 'Salary', 'Description', 'Requirements']

    for url in parse_xml_and_filter_urls(xml_gz_file, namespace, cutoff_date, num_urls):
        job_details = process_job_url(url)
        if job_details:
            write_to_csv(output_csv, fieldnames, job_details)
