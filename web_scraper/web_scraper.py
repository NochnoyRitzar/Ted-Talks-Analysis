from constants import TED_URL

import requests
from bs4 import BeautifulSoup, SoupStrainer

# @TODO: add async requests for faster execution

# speed up program by filtering what to parse
parse_only = SoupStrainer('div', id='browse-results')


def get_pages_count():
    """
    Find 'span' element with 'pagination__item pagination__gap' class and extract text from next (sibling) element

    :return: Return last page number
    :rtype: int
    """
    gap_span = catalog_page.find('span', class_='pagination__item pagination__gap')
    last_page_num = gap_span.find_next_sibling().get_text()
    return int(last_page_num)


def get_talks_info():
    """
    Get info about title, speaker, date posted, talk duration and talk page url

    :return: Return list of talk data
    :rtype: list
    """
    data = []

    # find all talks divs
    talk_divs = catalog_page.find_all('div', class_='media media--sm-v')
    for div in talk_divs:
        # get direct children
        talk_image, talk_info = div.find_all(recursive=False)

        # get url of a TED talk page
        talk_url = TED_URL + talk_image.a['href']
        # get talk duration and remove space in the beginning
        talk_duration = talk_image.a.span.contents[1].get_text(strip=True)

        speaker = talk_info.h4.get_text()
        title = talk_info.h4.find_next_sibling().a.get_text(strip=True)
        date_posted = talk_info.div.span.span.get_text(strip=True)

        data.append({'title': title,
                     'speaker': speaker,
                     'date': date_posted,
                     'duration': talk_duration,
                     'url': talk_url})

    return data


def get_talk_page_info():
    """
    Get views, likes count and tags from a talk page

    :return:
    :rtype: dict
    """
    pass


# for local development
resp = open("../TEDTalks1.htm")


# using 'lxml' parser because it's faster than other ones
catalog_page = BeautifulSoup(resp, 'lxml', parse_only=parse_only)

print(get_talks_info())
# loop over all talk pages
# for page_number in range(2, get_pages_count() + 1):
#     resp = requests.get(f'{TED_URL}?page={page_number}')
#
#     # using 'lxml' parser because it's faster than other ones
#     catalog_page = BeautifulSoup(resp, 'lxml', parse_only=parse_only)
