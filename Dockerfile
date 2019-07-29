FROM debian:stretch
# FROM vimagick/scrapyd
MAINTAINER Jesse Mortenson <jessemortenson@gmail.com>
# MAINTAINER Ayaz BADOURALY <ayaz.badouraly@via.ecp.fr>

RUN apt-get update && \
	apt-get install --assume-yes --no-install-recommends \
		gcc \
		libffi-dev \
		libssl-dev \
		libxml2-dev \
		libxslt1-dev \
		python-pip \
		python-dev \
		zlib1g-dev && \
	apt-get clean && \
	rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --upgrade \
		setuptools \
		wheel && \
	pip install --upgrade scrapy

# CMD ["scrapy", "shell", "--nolog"]

# install other packages we use on tst
RUN pip install requests arrow service_identity jsonpickle python-dotenv beautifulsoup4

RUN mkdir /var/spiders
WORKDIR /var/spiders

# Place spiders application code
COPY . /var/spiders/

COPY docker/docker_scrapyd_start.sh /var/spiders/docker_scrapyd_start.sh
RUN chmod ug+x /var/spiders/docker_scrapyd_start.sh
CMD ["/var/spiders/docker_scrapyd_start.sh"]