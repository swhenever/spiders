# showthing-scrape
Spiders for performing arts events, running in the Scrapy framewok (http://scrapy.org/). Spiders make ShowBills that are assigned to items, and items are fed to a pipelne that POSTs them to the engine's /showbill endpoint.

## Spider status

* turfclub: working!
* triplerock: working!

## Running spiders

* Set up scrapy-dev docker container (following its instructions) and make sure you can run the example spider. In this environment, you can just run "python" to have a python CLI to play with.
* Set up docker-php-mysql-nginx docker container (following its instructions)
* Run the engine application inside the docker-php-mysql-nginx container (following that app's instrucitons)
* Verify your copy of engine is running by visiting http://docker.dev:8080 on the host computer
* Run "docker ps" and copy the name of the nginx container, typically: dockerphpmysqlnginx_web_1
* Now run scrapy-dev with the command: docker run -it --rm --link [name-of-the-nginx-container]:docker.dev -v [path-to-showthing-scrape-code]:/code -w /code tst/scrapy-dev bash
    * Example: sudo docker run -it --rm --link dockerphpmysqlnginx_web_1:docker.dev -v ~/Documents/showoff/code/showoff_scrape:/code -w /code tst/scrapy-dev bash
*Inside this container, verify that you chose the right path-to-showthing-scrape by running "ls". Directory should contain a folder called showoff_scrape
* Run a spider with the scrapy command: scrapy crawl [name-of-spider]
    * Example: scrapy crawl turfclub
    
If you succeeded, you should see scrapy output free of errors, with a successful items scraped count at the end ("'item_scraped_count': 41").
