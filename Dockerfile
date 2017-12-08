FROM selenium/standalone-chrome:latest

USER root
RUN apt-get -qqy update \
  && apt-get -qqy --no-install-recommends install \
    libxml2-dev \
    libxslt-dev \
    python3 \
    python3-pip \
    python3-setuptools \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
  && ln -s /usr/bin/python3 /usr/bin/python

WORKDIR /home/seluser
COPY . ./
RUN pip3 install -e . && chown -R seluser: .

USER seluser
