# Career Compass, part 1: job_scraping
The goal of this stage of the Career Compass project is to scrape details from job ads and save to csv. It has been a great opportunity for me to learn about unit tests, ethical scraping, and using xml sitemaps, as well as working with LLMs to solve problems.

The project is modular and designed for scalability, with each function handling a specific step in the scraping process. Here's how the different components fit together:


## src/: 
Contains the core functions in three different .py files.


### src/main.py:
The entry point for the project. It orchestrates the entire process: 
- Reading key variables from a separate JSON file with read_config()
- Downloading XML sitemaps using download_sitemaps(), defined in sitemap_parser.py
- Extracting job details and saving results to CSV using process_xml_file(), defined in sitemap_parser.py

### src/sitemap_parser.py:
Handles XML sitemap parsing and processing.

- prepare_files:
  opens a CSV file ready for writing job data.

- parse_xml_and_filter_urls:
  extracts URLs from XML files, filtering for job ad links.

- download_sitemaps: 
fetches sitemap files in .xml.gz format from the target website. This function includes random delays to respect the website’s resources and avoid being blocked, and logs errors for any inaccessible or malformed files.

- write_to_csv: 
writes structured job details to the CSV file. This function is called by process_xml_file().

- process_xml_file: 
processes the downloaded XML files to extract job URLs, extract job details, and save them to csv, by calling:

  * prepare_files()
  * process_job_url() (defined in scraper.py)
  * parse_xml_and_filter_urls()
  * write_to_csv()
Supports limiting the number of URLs processed for testing purposes.


### src/scraper.py:
- process_job_url:
  calls scrape_job_page() to process a job ad URL by retrieving and parsing its HTML content to extract  structured job details.

  To ensure graceful handling of missing or inaccessible job pages, this function logs a warning and skips the URL if no job details are found. Returns a dictionary containing the job details if successful, or None if no details are found or an error occurs.

- scrape_job_page:
  retrieves the HTML content of a job ad by calling _scrape_job_page_core. Incorporates random delays (3–7 seconds), rate limiting, rotating headers and retries to handle server issues or blocking.
  Workflow:
  * scrape_job_page() checks if disable_logging is set to True, meaning logging suppression is required. Logging suppression is helpful in testing scenarios to avoid cluttering logs.
  * scrape_job_page() calls _scrape_job_page_core() with suppress_logging() if required. 
  * _scrape_job_page_core() parses html content if directly provided by calling extract_job_details()
  * If not, _scrape_job_page_core() validates the URL, configures request headers, and fetches the page using requests.get.
  * _scrape_job_page_core() parses the response content by calling extract_job_details() through fetch_and_parse() inner function (wrapped with @sleep_and_retry to retry the HTTP request and parsing up to the specified max_retries)
  * _scrape_job_page_core() extracts job details and logs success.

- extract_job_details: extracts structured data for a given job (title, employer, salary, requirements and description) from the HTML content using BeautifulSoup. Handles missing fields gracefully and replaces line breaks with spaces for cleaner data.

- extract_salary_from_text:
helper function to parse salary information from job descriptions using regular expressions (regex). Called in extract_job_details(). 


## File Organisation


## tests/: 

Contains unit tests for individual functions with a focus on validating core functions, handling edge cases, and supporting debugging.

### tests/test_extract_job_details.py:
Tests extract_job_details function on mock html snippets.

- test_extract_job_details_success: confirms extraction of job details 

- test_extract_job_details_missing_fields: confirms handling of missing fields

- test_extract_job_details_salary_fallback: tests the ability of extract_job_details() to call extract_salary_from_text() as fallback when no salary field, and successfully extract salary info from within the job description field

### tests/test_scrape_job_page.py:
Tests scrape_job_page() function.

- test_scrape_job_page_retries:
simulates real-world scenarios using mocks for HTTP requests, verifying retry logic by simulating server errors followed by successful responses

- test_scrape_job_page_parsing:
tests parsing logic directly with mock HTML content to validate extracted job details without making actual HTTP requests.

## Data Handling

- Scraped data are saved to a CSV file, structured to facilitate later cleaning and NLP processing.

- Each major function includes logging for errors, retries, and handling for missing fields to maintain transparency and aid debugging.


## Part 2 (coming soon):
- Clean and prepare the data
- Develop NLP model/embedding of job features
- Deploy user-friendly interface for users to tailor career plans



With thanks to JT for the encouragement!

