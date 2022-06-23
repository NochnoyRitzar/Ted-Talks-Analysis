import time

from constants import TED_URL

import requests
from bs4 import BeautifulSoup, SoupStrainer
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# @TODO: add async requests for faster execution
# @TODO: create Talk class to store talk related info

# speed up program by filtering what to parse
catalog_parse_only = SoupStrainer('div', id='browse-results')
page_parse_only = SoupStrainer('main', id='maincontent')


class WebScrappy:

    def __init__(self):
        try:
            # selenium web driver for dynamic scraping
            self.driver = WebScrappy.create_browser_driver()
            self.last_page = WebScrappy.get_pages_count()

            self.start_scraping()
        finally:
            self.driver.quit()

    @staticmethod
    def create_browser_driver():
        """
        Configure and create selenium firefox webdriver

        :return: Return selenium webdriver
        """

        print('Creating selenium webdriver')
        # add driver options
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument("--disable-extensions")

        driver = webdriver.Firefox(service=Service(executable_path='geckodriver.exe'), options=options)
        print('Finished creation')

        return driver

    @staticmethod
    def get_pages_count():
        """
        Perform request to catalog page to extract pagination last page number

        :return: Return last page number
        :rtype: int
        """

        response = requests.get(TED_URL + '/talks')
        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        gap_span = catalog_page.find('span', class_='pagination__item pagination__gap')
        last_page_num = gap_span.find_next_sibling().get_text()
        return int(last_page_num)

    @staticmethod
    def scrape_catalog_page(page_number):
        response = requests.get(TED_URL + f'/talks?page={page_number}')
        catalog_page = BeautifulSoup(response.content, 'lxml', parse_only=catalog_parse_only)

        return catalog_page

    def get_catalog_talks_info(self, catalog_page):
        """
        Get info about title, speaker, date posted, talk duration and talk page url from catalog page
        (https://www.ted.com/talks)

        :return: Return list of talks info
        :rtype: list
        """
        data = []

        # find all talks divs
        talk_divs = catalog_page.find_all('div', class_='media media--sm-v')
        for div in talk_divs:
            # get direct children
            talk_image, talk_info = div.find_all(recursive=False)

            # get url of a TED talk page
            talk_page_url = TED_URL + talk_image.a['href']

            # START SCRAPING TALK'S PAGE (MAKE ASYNC)
            talk_page_content = self.scrape_talk_page(talk_page_url)

            talk_page_info = WebScrappy.get_talk_page_info(talk_page_content)

            # get talk duration and remove space in the beginning
            talk_duration = talk_image.a.span.contents[1].get_text(strip=True)
            speaker = talk_info.h4.get_text()
            title = talk_info.h4.find_next_sibling().a.get_text(strip=True)
            date_posted = talk_info.div.span.span.get_text(strip=True)

            data.append({'title': title,
                         'speaker': speaker,
                         'date': date_posted,
                         'duration': talk_duration,
                         'page_url': talk_page_url,
                         **talk_page_info})

            # SOMETHING LIKE AWAIT RESULT FROM ASYNC FUNC
            # AND APPEND DICTIONARY RESULT TO DATA

            # for testing to get only first talk in catalog
            break

        return data

    def scrape_talk_page(self, talk_page_url):
        """

        :param talk_page_url:
        :return: Return page DOM after button click
        """
        self.driver.get(talk_page_url)
        # check if no such element exists in DOM
        try:
            self.driver.find_element(By.CSS_SELECTOR, 'button > span ~ i').click()
        except NoSuchElementException:
            pass

        return self.driver.page_source

    @staticmethod
    def get_talk_page_info(talk_page_content):
        """
        Get views, likes count, topics and related videos info from a talk's page

        :param talk_page_content:
        :return: Talk information from it's page on TED
        :rtype: dict
        """

        talk_page = BeautifulSoup(talk_page_content, 'lxml', parse_only=page_parse_only)

        page_left_side = talk_page.find('div', attrs={'class': 'md:mb-4'})
        # find direct children of div element with class containing 'flex'
        talk_stats, talk_topics, _ = page_left_side.find_all(attrs={'class': 'flex'}, recursive=False)
        views = talk_stats.div.div.get_text(strip=True).split(' ')[0]
        like_count = talk_stats.find('span').get_text(strip=True)[1:-1]
        summary = talk_topics.find(attrs={'class': 'text-sm mb-6'}).get_text(strip=True)

        page_right_side = talk_page.find('aside')
        # get topic list and iterate over it to get video topics
        talk_topics_list = page_right_side.find('ul')
        topics = [li.a.get_text(strip=True) for li in talk_topics_list.contents]

        return {'views': views,
                'like_count': like_count,
                'summary': summary,
                'topics': topics}

    def start_scraping(self):
        print('Starting to web scrape')
        # iterate over all catalog pages
        for page_number in range(1, self.last_page + 1):
            catalog_page = WebScrappy.scrape_catalog_page(page_number)
            catalog_page_talks_info = self.get_catalog_talks_info(catalog_page)
            print(f'Finished scraping {page_number}/{self.last_page} pages')
            print(catalog_page_talks_info)
            # for testing to stop iterating through pages
            break


if __name__ == '__main__':
    # start web scraping
    scrappy = WebScrappy()

