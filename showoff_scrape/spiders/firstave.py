import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
from showoff_scrape.items import ShowItem

class FirstAveSpider(CrawlSpider):

    name = 'firstave'
    venueIdentifyingUrl = 'http://www.first-avenue.com'
    venueLabel = 'First Avenue'
    allowed_domains = ['first-avenue.com']
    start_urls = ['http://first-avenue.com/calendar/all/2015-02']
    rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')] #/event/2015/02/rhettmiller

    def parse_show(self, response):
        show = ShowItem()

        show['url'] = response.url

        name_result = response.xpath("//h1[@id='page-title']/text()").extract()
        show['title'] = name_result[0]

        room_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-room ")]/text()').extract()
        if len(room_string) > 0:
            show['room'] = room_string[0]
        else: 
            show['room'] = ""
        #show['venue'] = 'First Avenue' 
        #venue: #field-name-field-event-venue//a/text() 
        #"room": #field-name-field-event-room/text()

        date_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " datepart ")]/text()').extract() #date-display-single
        date_string = date_string[0]
        time_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " date-display-single ")]/text()').extract()
        time_string = time_string[0]
        time_string_parts = time_string.split('at');
        time_string = time_string_parts[1]

        date = arrow.get(date_string.strip() + " " + time_string.strip(), 'dddd, MMMM D, YYYY h:mma')
        show['start'] = date

        # find performers
        performers = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-performer ")]//article[contains(concat(" ", normalize-space(@class), " "), " node-performer ")]//h2//a/text()').extract() #field-name-field-event-performer
        show['performers'] = performers

        return show
