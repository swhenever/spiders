from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ticketfly import TicketFlySpider
import arrow
import re
import datetime
import showspiderutils
import dateutil
from showoff_scrape.items import *

class UptownVFWSpider(TicketFlySpider):

    name = 'uptownvfw'
    start_urls = ['https://www.ticketfly.com/venue/12559-james-ballentine-vfw/']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Uptown VFW', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://uptownvfw.org/'
        return venue_section
    
    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('uptownvfw.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = self.make_ticketfly_event_section(response)

        # PERFORMANCES
        performances = self.make_ticketfly_performance_section(response)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        return scrapy_showbill_item
