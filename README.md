# Mixed Content Report


## Overview

This tool utilizes the BeautifulSoup, Celery, Chrome webdriver, Docker,
and Selenium to crawl a domain's sitemap and verify that pages do not throw
Mixed Content warnings.


## Executing via Docker

Clone the repository.
```sh
git clone https://github.com/mattoberle/mixed-content
cd mixed-content
```

Create a `domains.cfg` file in the repository root, placing each domain on a
new line.
```
www.example.com
www...
```

Alternatively (or in addition) a `urls.cfg` file can be placed in the
repository root, placing each URL on a new line.
```
https://www.example.com/page-1
https://www.example.com/page-2
```

Execute the process with the number of desired workers.
```sh
docker-compose up --scale worker=7
```

Results will be saved to `results/results.txt`.


The number of workers can be modified mid-execution.
```sh
docker-compose up --no-recreate --scale workers=N
```
