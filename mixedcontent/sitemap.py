import requests
from bs4 import BeautifulSoup


def parse_sitemap(url):
    resp = requests.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'lxml')
    urls = (tag.text.strip() for tag in soup.findAll('loc'))
    for url in urls:
        if url.endswith('.xml'):
            yield from parse_sitemap(url)
        else:
            yield url
