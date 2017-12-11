import socket
import time
from datetime import datetime
from subprocess import Popen

import redis
import requests
from bs4 import BeautifulSoup
from celery import Celery
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


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


app = Celery('tasks', broker='redis://broker')
driver = start_selenium_server()
redis_client = redis.StrictRedis(host='results', db=1, decode_responses=True)


@app.task(trail=True)
def parse_sitemap(domain, url):
    resp = requests.get(url)
    if resp.status_code == 503:
        parse_sitemap.apply_async(args=[domain, url], countdown=5)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'lxml')
    urls = (tag.text.strip() for tag in soup.findAll('loc'))

    for url in urls:
        if url.endswith('.xml'):
            parse_sitemap.delay(domain, url)
        elif domain in url:
            check_for_mixed_content.delay(url)
        else:
            continue  # URLs not on the original domain should not be called.
    return


@app.task(trail=True)
def check_for_mixed_content(url):
    try:
        driver.get(url)
    except TimeoutException:
        result = ('timeout', url)
        redis_client.rpush('results', result)
        return result
    log = driver.get_log('browser')
    for msg in log:
        if 'MixedContent' in msg['message']:
            result = ('error', url)
            redis_client.rpush('results', result)
            return result
    else:
        result = ('good', url)
        redis_client.rpush('results', result)
        return result


def report():
    with open('results/results.txt', 'w') as f:
        while True:
            _, result = redis_client.blpop('results')
            status, url = eval(result)
            ts = datetime.now().isoformat()
            f.write('{},{},{}\n'.format(ts, status, url))
