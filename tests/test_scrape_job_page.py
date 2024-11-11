import unittest
import logging
from unittest import TestCase, mock
from bs4 import BeautifulSoup
import requests
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scraper import scrape_job_page

class TestScrapeJobPage(TestCase):
    # Mock HTML content for testing the parsing logic
    mock_html_content = '''
    <html>
        <body>
            <h2 class="header-style__JobViewHeaderJobName-sc-c5940466-9">Software Engineer</h2>
            <ul>
                <li class="header-style__JobViewHeaderCompanyName-sc-c5940466-12">Tech Corp</li>
            </ul>
            <div class="description-styles__DescriptionContainerInner-sc-78eb761c-2">
                Develop and maintain software solutions, with an annual compensation of 80,000 USD per year.
            </div>
            <ul class="skill-list-clamped-styles__SkillsContainerInner-sc-5a5d6754-0">
                <li>Python</li>
                <li>Django</li>
            </ul>
            <ul class="header-style__JobViewHeaderTagsContainer-sc-c5940466-11">
                <li><span class="indexmodern__TagLabel-sc-6pvrvp-1 bkgNmO ds-tag-label">80,000 USD per year</span></li>
            </ul>
        </body>
    </html>
    '''



    @mock.patch('Monster_job_scraper_main.requests.get')
    def test_scrape_job_page_retries(self, mock_get):
        # Mock a 500 error response initially, then a successful response with HTML content
        mock_response_500 = mock.Mock()
        mock_response_500.status_code = 500
        mock_response_500.raise_for_status.side_effect = requests.exceptions.HTTPError()

        mock_response_200 = mock.Mock()
        mock_response_200.status_code = 200
        mock_response_200.content = self.mock_html_content

        # Simulate retry: return a 500 error on the first call and success on the second call
        mock_get.side_effect = [mock_response_500, mock_response_200]

        # Call scrape_job_page with a dummy URL to simulate error, triggering retry
        dummy_request = scrape_job_page(url="http://example.com", max_retries=2, disable_logging=True)

        # Ensure requests.get was called twice (one retry)
        self.assertEqual(mock_get.call_count, 2)

    def test_scrape_job_page_parsing(self):
        # Test parsing directly with mock HTML content, without using requests.get
        job_details = scrape_job_page(url="", html_content=self.mock_html_content)

        # Define expected output
        expected_details = {
            'job_title': 'Software Engineer',
            'employer': 'Tech Corp',
            'description': 'Develop and maintain software solutions, with an annual compensation of 80,000 USD per year.',
            'requirements': ['Python', 'Django'],
            'salary': '80,000 USD per year'
        }

        # Check if the job details match the expected details
        self.assertEqual(job_details, expected_details)

if __name__ == '__main__':
    unittest.main()
