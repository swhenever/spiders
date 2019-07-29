import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import dateutil
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response


class TurfClubSpider(CrawlSpider):

    name = 'turfclub'
    allowed_domains = ['turfclub.net']
    start_urls = ['http://turfclub.net/shows/']
    rules = [Rule(LinkExtractor(allow=['/show/\d\d\d\d-\d\d-.+']), 'parse_show')] #/show/2015-04-traster-pureka/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Turf Club', 'Saint Paul', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://turfclub.net/'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'turfclub.py'
        return discovery_section

    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]', r'', text).strip()

    def parse_show(self, response):
        # @todo source_documents
        #inspect_response(response, self)

        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        name_result = response.css('h2.rhp-event-header a::text').extract()
        event_section.title = self.kill_unicode_and_strip(name_result[0])

        # parse doors date/time
        date_string = response.css('div.rhp-event-details p.rhp-event-date::text').extract()
        date_string = self.kill_unicode_and_strip(date_string[0])
        time_string = response.css('div.rhp-event-details p.rhp-event-time::text').extract()
        time_string = self.kill_unicode_and_strip(time_string[0])
        combined_string = date_string + " " + time_string
        date = arrow.get(combined_string, [r"\w+, MMMM D, YYYY h:mm a"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.doorsDatetime = date

        # PERFORMERS SECTION
        # find performers
        performer_strings = response.css('div.tribe-events-single-event-description h2::text, div.tribe-events-single-event-description h3::text').extract()
        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = self.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)


        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
