import pickle
from contextlib import contextmanager

import requests
from bs4 import BeautifulSoup
from selenium import webdriver


class Cache:
    def __init__(self, cache_file):
        self.cache_file = cache_file
        self.checked = set()
        self.errors = set()

    def load(self):
        try:
            with open(self.cache_file, mode='rb') as f:
                checked, errors = pickle.load(f)
            self.checked.update(checked)
            self.errors.update(errors)
        except (IOError, FileNotFoundError, EOFError):
            return

    def save(self):
        with open(self.cache_file, mode='wb') as f:
            pickle.dump((self.checked, self.errors), f)


def parse_sitemap(url):
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'lxml')
    urls = (tag.text for tag in soup.findAll('loc'))
    for url in urls:
        if url.endswith('.xml'):
            yield from parse_sitemap(url)
        else:
            yield url


def check_for_mixed_content(urls, cache_file='.mixedcontent', clear=False):
    driver = webdriver.Chrome()
    with cache(cache_file, clear) as c:
        for i, url in enumerate(urls):
            if url in c.checked:
                continue
            driver.get(url)
            c.checked.add(url)
            log = driver.get_log('browser')
            msgs = (d['message'] for d in log if d['level'] == 'SEVERE')
            if any('Mixed Content' in msg for msg in msgs):
                c.errors.add(url)
                yield url
            if i % 5 == 0:
                c.save()


@contextmanager
def cache(cache_file, clear):
    cache = Cache(cache_file)
    if not clear:
        cache.load()
    yield cache
    cache.save()
