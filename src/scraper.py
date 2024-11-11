
# imports
import logging
import time
import random
from fake_useragent import UserAgent
from validators import url as validate_url
from ratelimit import limits, sleep_and_retry
from contextlib import contextmanager
import requests
from bs4 import BeautifulSoup
import re

# This file contains functions related to scraping a job page and returning details

# define scraping function

@contextmanager
def suppress_logging():
    """Temporarily suppress logging, for test purposes."""
    previous_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.CRITICAL)
    try:
        yield
    finally:
        logging.getLogger().setLevel(previous_level)

def process_job_url(url):
    """Scrape job page and return job details dictionary."""
    try:
        job_details = scrape_job_page(url)
        if job_details is None:
            logging.warning(f"No details found for {url}. Skipping...")
            return None
        return job_details
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return None

def scrape_job_page(url, max_retries=3, html_content=None, disable_logging=False):
    """Scrape an individual job page for details, with retries, or parse static HTML if provided."""
    # Disable logging if flag is set
    if disable_logging:
        with suppress_logging():
            return _scrape_job_page_core(url, max_retries, html_content)
    else:
        return _scrape_job_page_core(url, max_retries, html_content)

@limits(calls=10, period=90)
def _scrape_job_page_core(url, max_retries, html_content):
    """Core logic for scraping job page to be reused by the main function."""

    # If html_content is provided, skip requests and parse directly
    if html_content:
        job_soup = BeautifulSoup(html_content, 'html.parser')
        job_details = extract_job_details(job_soup)
        logging.info("Successfully parsed job details from static HTML content.")
        return job_details

    if not validate_url(url):
        logging.error(f"Invalid job page URL: {url}")
        return None

    # Set up headers and user-agent for scraping
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.monster.com',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Upgrade-Insecure-Requests': '1',
    }

    delay = 2
    attempt = 0

    @sleep_and_retry
    def fetch_and_parse():
        logging.info(f"Fetching URL: {url} (Attempt {attempt + 1})")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        job_soup = BeautifulSoup(response.content, 'html.parser')
        job_details = extract_job_details(job_soup)
        logging.info(f"Successfully scraped job details for {url}")
        return job_details

    while attempt < max_retries:
        try:
            return fetch_and_parse()
        except requests.exceptions.RequestException as e:
            attempt += 1
            logging.error(f"Error scraping {url}. Attempt {attempt} failed: {e}")
            time.sleep(delay * (2 ** attempt) + random.uniform(0, 1))
        except Exception as e:
            logging.error(f"An unexpected error occurred while scraping {url}: {e}")
            break

    logging.error(f"Failed to scrape {url} after {max_retries} attempts.")
    return None


# define regex pattern for salary-like information and search function for salary info - include time unit (hour, week, month, year) after the salary amount

salary_pattern = re.compile(
    r'(?i)(compensation|salary|pay|rate)[\s\w]*?(:?|\s) (\$[\d,]+(?:\.\d{2})?)(\s*(?:per|weekly|monthly|yearly|hourly|annually)?\s*){1,4}((hour|week|month|year))?'
)

# define function to search for salary details
def extract_salary_from_text(text):
    """Applies regex to extract salary-like info from a text (job title or description)."""
    match = salary_pattern.search(text)
    if match:
        # This constructs the salary string with the time unit
        salary_amount = match.group(2)  # This returns the salary amount found
        time_unit = match.group(3) if match.group(3) else ''  # Optional time unit
        return f"{salary_amount} {time_unit}".strip()  # Combine and return
    return 'None'


# define function to extract elements from job page

def extract_job_details(job_soup):
    """Extracts job title, employer, salary, requirements, and description from a job listing."""
    job_details = {}

    # Extract job title
    try:
        job_title_element = job_soup.select_one("h2.header-style__JobViewHeaderJobName-sc-c5940466-9")
        job_details['job_title'] = job_title_element.text.strip() if job_title_element else 'None'
    except Exception as e:
        job_details['job_title'] = 'None'
        logging.error(f"Error extracting job title: {e}")

    # Extract employer
    try:
        employer_element = job_soup.select_one("li.header-style__JobViewHeaderCompanyName-sc-c5940466-12")
        job_details['employer'] = employer_element.text.strip() if employer_element else 'None'
    except Exception as e:
        job_details['employer'] = 'None'
        logging.error(f"Error extracting employer: {e}")

    # Extract description
    try:
        description_element = job_soup.select_one("div.description-styles__DescriptionContainerInner-sc-78eb761c-2")
        if description_element:
            # Replace line breaks with spaces or another delimiter (e.g., ' | ')
            job_description = description_element.text.strip().replace('\n', ' ').replace('\r', ' ')
            job_details['description'] = job_description
        else:
            job_details['description'] = 'None'
            job_description = ''  # Fallback in case description is missing
    except Exception as e:
        job_details['description'] = 'None'
        job_description = ''
        logging.error(f"Error extracting description: {e}")

    # Extract salary with dedicated field + fallback to title/description regex search
    try:
        salary_element = job_soup.select_one(
            "ul.header-style__JobViewHeaderTagsContainer-sc-c5940466-11 li span.indexmodern__TagLabel-sc-6pvrvp-1.bkgNmO.ds-tag-label"
        )
        if salary_element:
            job_details['salary'] = salary_element.text.strip()
            logging.info(f"extracted salary element from field: {job_details['salary']}")
        else:
            # Fallback to search the job title and description
            job_title = job_details.get('job_title', '')
            job_details['salary'] = extract_salary_from_text(job_title + ' ' + job_description)
            logging.info(f"fallback search identified salary: {job_details['salary']}")
    except Exception as e:
        job_details['salary'] = 'None'
        logging.error(f"Error extracting salary: {e}")

    # Extract requirements
    try:
        requirements_element = job_soup.select_one("ul.skill-list-clamped-styles__SkillsContainerInner-sc-5a5d6754-0")
        if requirements_element:
            requirements_list = requirements_element.find_all('li')
            job_details['requirements'] = [
                req.text.strip().replace('unmatched', '').strip()
                for req in requirements_list if req.text.strip()
            ]
        else:
            job_details['requirements'] = 'None'
    except Exception as e:
        job_details['requirements'] = 'None'
        logging.error(f"Error extracting requirements: {e}")

    return job_details
