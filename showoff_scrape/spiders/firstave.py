import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import dateutil
from showoff_scrape.items import *

class FirstAveSpider(CrawlSpider):

    name = 'firstave'
    allowed_domains = ['first-avenue.com']
    start_urls = ['http://first-avenue.com/calendar/all/2015-02']
    rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')] #/event/2015/02/rhettmiller

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('First Avenue', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venue_url = 'http://www.first-avenue.com/'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discovered_by = 'firstave.py'
        return discovery_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.found_url = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.event_url = response.url

        name_result = response.xpath("//h1[@id='page-title']/text()").extract()
        event_section.title = name_result[0]

        stage_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-room ")]/text()').extract()
        if len(stage_string) > 0:
            event_section.stage = stage_string[0]
        #show['venue'] = 'First Avenue' 
        #venue: #field-name-field-event-venue//a/text() 
        #"room": #field-name-field-event-room/text()

        date_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " datepart ")]/text()').extract() #date-display-single
        date_string = date_string[0]
        time_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " date-display-single ")]/text()').extract()
        time_string = time_string[0]
        time_string_parts = time_string.split('at');
        time_string = time_string_parts[1]

        date = arrow.get(date_string.strip() + " " + time_string.strip(), 'dddd, MMMM D, YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.doors_datetime = date

        # PERFORMANCES SECTION
        performer_strings = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-performer ")]//article[contains(concat(" ", normalize-space(@class), " "), " node-performer ")]//h2//a/text()').extract() #field-name-field-event-performer
        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = performer
            performance_section.order = i
            performances.append(performance_section)
        performances_section = PerformancesSection(performances)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances_section)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
