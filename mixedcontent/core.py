import gzip
import socket
from io import BytesIO
from logging import getLogger
from typing import Generator

import requests
from bs4 import BeautifulSoup
from chromedriver_binary import chromedriver_filename
from selenium import webdriver
from selenium.common.exceptions import TimeoutException


logger = getLogger('console')


def start_selenium_server() -> webdriver.Chrome:
    """
    Starts a stand-alone Chrome Selenium server listening on
    a free port.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', 0))
        ip, port = sock.getsockname()
    return webdriver.Chrome(port=port, executable_path=chromedriver_filename)


def parse_sitemap(domain: str, url: str) -> Generator[str, None, None]:
    """
    Accepts a domain and sitemap URL.
    For each page in the sitemap a mixed content check or
    recursive parse sitemap task will be scheduled.
    """
    resp = requests.get(url)
    resp.raise_for_status()

    body = (gzip.open(BytesIO(resp.content)).read()
            if url.endswith('.gz') else resp.content)
    soup = BeautifulSoup(body, 'lxml')

    urls = (tag.text.strip() for tag in soup.findAll('loc'))
    for url in urls:
        if url.endswith('.xml') or url.endswith('.xml.gz'):
            yield from parse_sitemap(domain, url)
        elif domain in url:
            yield url
        continue


def check_for_mixed_content(driver: webdriver.Chrome, url: str):
    """
    Opens a page via the Chrome web driver and checks the console log
    for "Mixed Content" errors.
    """
    url = url.replace('http:', 'https:', 1) if url.startswith('http:') else url
    try:
        driver.get(url)
    except TimeoutException:
        logger.error('Timeout: %s', url)

    log = driver.get_log('browser')
    mixed_content = any(msg for msg in log if 'Mixed Content' in msg['message'])
    if mixed_content:
        logger.warning('MixedContent: %s', url)
    else:
        logger.info('Ok: %s', url)
