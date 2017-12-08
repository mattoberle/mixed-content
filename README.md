# Mixed Content Report


## Overview

This tool utilizes the Chrome webdriver, BeautifulSoup, and Selenium to
crawl a sitemap and verify that pages do not throw Mixed Content warnings.


## Installation

```sh
pip install git+https://github.com/mattoberle/mixed-content.git
```


## Executing via Docker

Create a `sitemap.cfg` file in the repository root, placing each URL on a
new line.
```
https://www.example.com/sitemap.xml
https://...
```

Execute the process with the number of desired workers.
```sh
docker-compose up --scale worker=7
```

Results will be saved to `results/results.txt`.
