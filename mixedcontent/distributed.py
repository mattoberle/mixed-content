import socket
import time
from datetime import datetime
from subprocess import DEVNULL, Popen

import redis
import requests
from bs4 import BeautifulSoup
from celery import Celery
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


class ResultCollectedError(IOError):
    pass


class WebDriver(webdriver.Remote):
    """
    Extends the remote webdriver to include support for reading
    results.txt and skipping checked URLs. This is useful for resuming
    an interrupted process.
    """
    def __init__(self, *args, **kwargs):
        self._results_cache = set()
        # IOError is thrown when no results.txt is present.
        # ValueError is thrown if the results.txt does not conform
        # to the exepected three-column schema.
        try:
            with open('data/results.txt', 'r') as f:
                for line in f:
                    ts, status, url = line.strip().split(',')
                    self._results_cache.add(url)
        except (IOError, ValueError):
            pass
        super(WebDriver, self).__init__(*args, **kwargs)

    def get(self, url, *args, **kwargs):
        """
        Raises a ResultCollectedError, which can be caught
        and handled to skip URLs.
        """
        if url in self._results_cache:
            raise ResultCollectedError()
        super(WebDriver, self).get(url, *args, **kwargs)


def start_selenium_server(timeout=10):
    """
    Starts a stand-alone Chrome Selenium server listening on
    port 4444. This will block until the server is available
    or until the timeout is reached.
    """
    Popen(['/opt/bin/entry_point.sh'], stdout=DEVNULL)
    started = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    start_time = time.time()
    started = False
    while not started:
        started = sock.connect_ex(('127.0.0.1', 4444)) == 0
        if time.time() - start_time > timeout:
            raise IOError('Could not connect to Selenium server.')

    driver = WebDriver(
        command_executor='http://127.0.0.1:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME
    )
    driver.implicitly_wait(30)
    return driver


app = Celery('tasks', backend='redis://broker', broker='redis://broker')
driver = start_selenium_server()
redis_client = redis.StrictRedis(host='broker', db=1, decode_responses=True)


@app.task()
def parse_sitemap(domain, url):
    """
    Accepts a domain and sitemap URL.
    For each page in the sitemap a mixed content check or
    recursive parse sitemap task will be scheduled.
    """
    resp = requests.get(url)

    # If a site is overloaded the calls can be delayed, although it's
    # probably better to scale down the worker count.
    if resp.status_code == 503:
        parse_sitemap.apply_async(args=[domain, url], countdown=5)

    # There is currently no handling in place
    # for invalid sitemap URLs.
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, 'lxml')
    urls = (tag.text.strip() for tag in soup.findAll('loc'))

    for url in urls:
        if url.endswith('.xml'):
            parse_sitemap.delay(domain, url)
        elif domain in url:
            check_for_mixed_content.delay(url)
        else:
            # URLs that are on sites other than the original
            # domain should be ignored, this tool allows for
            # some not-very-nice request rates.
            continue
    return


@app.task()
def check_for_mixed_content(url):
    """
    Opens a page via the Chrome web driver and checks the console log
    for "Mixed Content" errors. Results are published to Redis under
    one of three channels: timeout, error, good
    """
    try:
        driver.get(url)
    except TimeoutException:
        result = ('timeout', url)
        redis_client.publish(*result)
        return result
    except WebDriverException:
        start_selenium_server()
        check_for_mixed_content.delay(url)
        return  # retry after starting chrome
    except ResultCollectedError:
        return  # skipped (already seen)

    log = driver.get_log('browser')
    for msg in log:
        if 'Mixed Content' in msg['message']:
            result = ('error', url)
            redis_client.publish(*result)
            return result
    else:
        result = ('good', url)
        redis_client.publish(*result)
        return result


def report():
    """
    Subscribes to the three result channels (timeout, error, good)
    and streams results to a file.
    """
    pubsub = redis_client.pubsub()
    pubsub.psubscribe('timeout', 'error', 'good')
    with open('data/results.txt', 'a') as f:
        while True:
            for result in pubsub.listen():
                if result['type'] == 'psubscribe':
                    continue
                ts = datetime.now().isoformat()

                line = '{ts},{channel},{data}\n'.format(ts=ts, **result)
                f.write(line)
                f.flush()
                print(line)
