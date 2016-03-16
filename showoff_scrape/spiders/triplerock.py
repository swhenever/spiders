import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class TripleRockSpider(CrawlSpider):

    name = 'triplerock'
    allowed_domains = ['triplerocksocialclub.com']
    start_urls = ['http://www.triplerocksocialclub.com/shows']
    rules = [Rule(LinkExtractor(allow=['/event/\d+-.+']), 'parse_show')] #/event/829471-denim-matriarch-minneapolis/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Triple Rock Social Club', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.triplerocksocialclub.com'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'triplerock.py'
        return discovery_section


    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse_show(self, response):
        #inspect_response(response, self)

        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        name_result = response.css('div.event-info h1.headliners::text').extract()
        event_section.title = self.kill_unicode_and_strip(name_result[0])

        # parse doors date/time
        datetime_string = response.css('div.event-info h2.times span.start span::attr(title)').extract()
        datetime_string = self.kill_unicode_and_strip(datetime_string[0])
        date = arrow.get(datetime_string, 'YYYY-MM-DDTHH:mm:ssZZ') # 2015-05-02T20:00:00-05:00
        event_section.doorsDatetime = date

        # PERFORMERS SECTION
        # find performers
        performerStrings = response.css('div.artist-boxes div.artist-headline span.artist-name::text').extract()
        performances = []
        for i, performer in enumerate(performerStrings):
            performance_section = PerformanceSection()
            performance_section.name = self.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
