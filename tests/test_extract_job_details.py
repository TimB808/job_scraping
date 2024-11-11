import unittest
from bs4 import BeautifulSoup
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.scraper import extract_job_details
import logging


class TestExtractJobDetails(unittest.TestCase):
    def test_extract_job_details_success(self):

        html = """
        <html>
            <body>
                <h2 class="header-style__JobViewHeaderJobName-sc-c5940466-9">Software Engineer</h2>
                <li class="header-style__JobViewHeaderCompanyName-sc-c5940466-12">Tech Corp</li>
                <div class="description-styles__DescriptionContainerInner-sc-78eb761c-2">
                    Develop and maintain software solutions
                </div>
                <ul class="header-style__JobViewHeaderTagsContainer-sc-c5940466-11">
                    <li><span class="indexmodern__TagLabel-sc-6pvrvp-1 bkgNmO ds-tag-label">80,000 USD</span></li>
                </ul>
                <ul class="skill-list-clamped-styles__SkillsContainerInner-sc-5a5d6754-0">
                    <li>Python</li>
                    <li>Django</li>
                </ul>
            </body>
        </html>
        """

        # Parse HTML with BeautifulSoup
        job_soup = BeautifulSoup(html, 'html.parser')

        # Call the function
        job_details = extract_job_details(job_soup)

        # Expected details
        expected_details = {
            'job_title': 'Software Engineer',
            'employer': 'Tech Corp',
            'description': 'Develop and maintain software solutions',
            'salary': '80,000 USD',
            'requirements': ['Python', 'Django']
        }

        # Assert values
        self.assertEqual(job_details, expected_details)


    def test_extract_job_details_missing_fields(self):
        # Mock HTML with some fields missing
        html = '''
        <html>
            <body>
                <h2 class="header-style__JobViewHeaderJobName-sc-c5940466-9">Software Engineer</h2>
                <!-- Missing employer and salary elements -->
                <ul class="skill-list-clamped-styles__SkillsContainerInner-sc-5a5d6754-0">
                    <li>Python</li>
                    <li>Django</li>
                </ul>
            </body>
        </html>
        '''

        # Parse mock HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Call the function
        job_details = extract_job_details(soup)

        # Verify that missing fields return 'None' and existing fields are correct
        self.assertEqual(job_details.get('employer'), 'None')        # Missing employer
        self.assertEqual(job_details.get('salary'), 'None')          # Missing salary
        self.assertEqual(job_details.get('job_title'), 'Software Engineer')  # Existing title
        self.assertEqual(job_details.get('requirements'), ['Python', 'Django'])

    def test_extract_job_details_salary_fallback(self):
        # Mock HTML without a dedicated salary field, but with salary info in the description
        html_with_salary_in_description = """
        <html>
            <body>
                <h2 class="header-style__JobViewHeaderJobName-sc-c5940466-9">Software Engineer</h2>
                <li class="header-style__JobViewHeaderCompanyName-sc-c5940466-12">Tech Corp</li>
                <div class="description-styles__DescriptionContainerInner-sc-78eb761c-2">
                    Develop and maintain software solutions. Annual compensation $80,000 per year.
                </div>
                <ul class="skill-list-clamped-styles__SkillsContainerInner-sc-5a5d6754-0">
                    <li>Python</li>
                    <li>Django</li>
                </ul>
            </body>
        </html>
        """

        # Parse the mock HTML with BeautifulSoup
        job_soup = BeautifulSoup(html_with_salary_in_description, 'html.parser')

        # Call the function
        job_details = extract_job_details(job_soup)
        logging.info(f"regex test details: {job_details}")

        # Verify the extracted details, especially the salary
        expected_salary = "$80,000"
        self.assertEqual(job_details.get('salary'), expected_salary)



if __name__ == '__main__':
    unittest.main()
