# Mixed Content Report

## Overview

This tool utilizes the Chrome webdriver, BeautifulSoup, and Selenium to
crawl a sitemap and verify that pages do not throw Mixed Content warnings.

The code is currently an early prototype. Execution requires a a copy of the
Chrome webdriver on the user's PATH and is currently single-threaded. Caching
is performed via a single Python pickle.

Eventually this project will run in Docker and enable parallel execution via
compose.


## Installation

```sh
pip install git+https://github.com/mattoberle/mixed-content.git
```


## Usage

```
usage: mixedcontent [-h] --sitemaps SITEMAPS [SITEMAPS ...]
                    [--cache-file CACHE_FILE] [--clear-cache]

optional arguments:
  -h, --help            show this help message and exit
  --sitemaps SITEMAPS [SITEMAPS ...]
  --cache-file CACHE_FILE
  --clear-cache
```
