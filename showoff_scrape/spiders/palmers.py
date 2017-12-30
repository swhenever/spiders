from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import datetime
from bs4 import BeautifulSoup
import showspiderutils
import dateutil
from showoff_scrape.items import *


class PalmersSpider(CrawlSpider):

    name = 'palmers'
    allowed_domains = ['palmersbar.net']
    start_urls = ['http://palmersbar.net/events/category/music']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    fourd = '[0-9][0-9][0-9][0-9]'
    twod = '[0-9][0-9]'
    any_date_regex = fourd + '-' + twod + '-' + twod

    rules = [
        Rule(LinkExtractor(allow=['/event/.+/' + any_date_regex + '/']), 'parse_show'),
        Rule(LinkExtractor(allow=['/events/category/music/list/\?tribe_event_display=list&tribe_paged=[2-9]']))
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Palmers Bar', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://palmersbar.net'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('palmers.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()

        # title
        title_string = response.css('.tribe-events-single-event-title::text').extract_first()
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)

        # date
        date_string = response.css('.tribe-events-start-date::attr(title)').extract_first() # 2017-12-30

        # time
        # typically duration style: 10:00 pm - 11:55 pm
        soup = BeautifulSoup(response.css('.tribe-events-start-time').extract_first(), "lxml")
        time_string = soup.get_text().strip()
        times = showspiderutils.check_text_for_times(time_string)
        if len(times) is 0:
            return [] # abort: need at least one event time

        event_section.startDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-MM-DD"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # age restriction
        # palmer's assumed to be always 21+
        event_section.minimumAgeRestriction = 21

        # price
        cost_string = response.css('.tribe-events-cost::text').extract_first()
        prices = showspiderutils.check_text_for_prices(cost_string)
        if prices['doors'] is not None:
            event_section.ticketPriceDoors = prices['doors']
        if prices['advance'] is not None:
            event_section.ticketPriceDoors = prices['advance']

        # ticket url
        # I think Palmer's is always door-only

        # PERFORMANCES
        # apparently we can only get this from the title string
        performances = []
        performer_strings = showspiderutils.parse_text_for_performers(title_string)
        for index, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = performer
            performance_section.order = index
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        return scrapy_showbill_item

