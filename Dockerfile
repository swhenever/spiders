FROM vimagick/scrapyd
MAINTAINER Jesse Mortenson <jessemortenson@gmail.com>

# install other packages we use on tst
RUN pip install requests arrow service_identity jsonpickle python-dotenv beautifulsoup4

RUN mkdir /var/spiders
WORKDIR /var/spiders

# Place spiders application code
COPY . /var/spiders/

COPY docker/docker_scrapyd_start.sh /var/spiders/docker_scrapyd_start.sh
RUN chmod ug+x /var/spiders/docker_scrapyd_start.sh
CMD ["/var/spiders/docker_scrapyd_start.sh"]