# showthing-scrape
Spiders for performing arts events, running in the Scrapy framewok (http://scrapy.org/). Spiders make ShowBills that are assigned to items, and items are fed to a pipelne that POSTs them to the engine's /showbill endpoint.

## Spider status

* firstave: working!
* hexagonbar: NOT working (needs manually-renewed facebook API key)
* kittycatklub: working!
* leesliquorlounge: working (limitation: it lists all performances as separate shows, even if they are consecutive)
* threethirtyoneclub: working!
* triplerock: working!
* turfclub: working!

## Running spiders

* Set up scrapy-dev docker container (following its instructions) and make sure you can run the example spider. In this environment, you can just run "python" to have a python CLI to play with.
* Set up docker-php-mysql-nginx docker container (following its instructions)
* Run the engine application inside the docker-php-mysql-nginx container (following that app's instrucitons)
* Verify your copy of engine is running by visiting http://docker.dev:8080 on the host computer
* Run "docker ps" and copy the name of the nginx container, typically: dockerphpmysqlnginx_web_1
* Now run scrapy-dev with the command: docker run -it --rm --link [name-of-the-nginx-container]:docker.dev -v [path-to-showthing-scrape-code]:/code -w /code tst/scrapy-dev bash
    * Example: sudo docker run -it --rm --link dockerphpmysqlnginx_web_1:docker.dev -v ~/Documents/showoff/code/showoff_scrape:/code -w /code tst/scrapy-dev bash
    * --link sets up a link between the docker-php-mysql-nginx web container and the scrapy-dev container, so that our pipeline can make requests to engine's API. The argument is in the form [container-name]:[alias-name]
    * -v sets up a volume at /code inside the container. We make the showthing-scrape code available in that directory
    * -w sets the starting working directory
    * bash runs bash, so that you start in a bash CLI interface.
* Inside this container, verify that you chose the right path-to-showthing-scrape by running "ls". Directory should contain a folder called showoff_scrape
* Run a spider with the scrapy command: scrapy crawl [name-of-spider]
    * Example: scrapy crawl turfclub
    * You can also just run "python" to have a proper python environment for experimentation or debugging
    
If you succeeded, you should see scrapy output free of errors, with a successful items scraped count at the end ("'item_scraped_count': 41").
