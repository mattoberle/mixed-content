import socket
import time
from subprocess import Popen

from celery import Celery
from celery.result import ResultSet
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from mixedcontent.sitemap import parse_sitemap


def start_selenium_server():
    Popen(['/opt/bin/entry_point.sh'])
    started = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    start_time = time.time()
    started = False
    while not started:
        started = sock.connect_ex(('127.0.0.1', 4444)) == 0
        if time.time() - start_time > 10:
            raise IOError('Could not connect to Selenium server.')

    driver = webdriver.Remote(
        command_executor='http://127.0.0.1:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME
    )
    driver.implicitly_wait(10)
    return driver


app = Celery('tasks', backend='redis://redis', broker='redis://redis')
driver = start_selenium_server()


@app.task(trail=True)
def collect_urls(sitemaps):
    results = ResultSet([])
    for sitemap in sitemaps:
        urls = parse_sitemap(sitemap)
        for url in urls:
            results.add(check_for_mixed_content.delay(url))
    return results


@app.task(trail=True)
def check_for_mixed_content(url):
    try:
        driver.get(url)
    except TimeoutException:
        return ('timeout', url)
    log = driver.get_log('browser')
    for msg in log:
        if 'MixedContent' in msg['message']:
            return ('error', url)
    else:
        return ('good', url)
