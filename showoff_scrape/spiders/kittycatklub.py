import scrapy
from scrapy.selector import Selector
import arrow
from showoff_scrape.items import ShowItem

class KittyCatKlubSpider(scrapy.Spider):

    name = 'kittycatklub'
    venueIdentifyingUrl = 'http://www.kittycatklub.net'
    venueLabel = 'Kitty Cat Klub'
    allowed_domains = ['kittycatklub.net']
    start_urls = ['http://www.kittycatklub.net']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    def parse(self, response):
    	# Get the month / year that is being displayed
    	monthYearText = response.selector.css("span.headline::text").extract()[0]
    	parts = monthYearText.split(' ');
    	month = parts[0].strip(' \t\n\r') # 'March'
    	year = parts[1].strip(' \t\n\r') # '2015'
    	defaultTime = '9:00pm' # Kitty Cat Klub doesn't really list times, so we're going to provide one

    	# start with an empty show
    	show = ShowItem()

    	# kitty cat klub data is in the eighth nested table (!)
    	#tds = response.selector.xpath("//table//table//table//table//table//table//table//table//tr/td/text()").extract();
    	rowSelectors = response.selector.xpath("//table//table//table//table//table//table//table//table//tr")
    	for index, row in enumerate(rowSelectors):
    		# check what "kind" of row this is
    		if len(row.xpath("td").css("span.date::text").extract()) > 0:
    			# do date processing
    			dayString = row.xpath("td").css("span.date::text").extract()[0]
    			dayparts = dayString.split(' ')
    			day = dayparts[0].strip(' \t\n\r')
    			date = arrow.get(month + " " + day + " " + year + " " + defaultTime, 'MMMM D YYYY h:mma')
        		show['start'] = date

    			# do price processing
    			costString = row.xpath("td").css("span.cost::text").extract()[0]

    			# construct a fake anchor + url to use as a unique identifier
    			url = self.venueIdentifyingUrl + "/#" + year + "-" + month + "-" + day
    			show['url'] = url
    		elif len(row.xpath("td[contains(@colspan, '5')]/text()").extract()) > 0:
    			# do performer list processing
    			performers = []
    			performerStrings = row.xpath("td/text()").extract()
    			for performerString in performerStrings:
    				performerString = performerString.strip(' \t\n\r')
    				if len(performerString) > 0:
    					performers.append(performerString)
    			show['performers'] = performers
    			show['title'] = ', '.join(performers)

    		if 'start' in show and 'url' in show and 'performers' in show:
    			# our show is (almost) fully populated. yield
    			yield show

    			# initialize a new show
    			show = ShowItem()