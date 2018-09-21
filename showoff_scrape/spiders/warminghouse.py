import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import re
from bs4 import BeautifulSoup
import dateutil
from showoff_scrape.items import *
import showspiderutils


class WarmingHouse(CrawlSpider):

    name = 'warminghouse'
    allowed_domains = ['thewarminghouse.net']
    start_urls = ['https://www.thewarminghouse.net/calendar/']
    # /event/1755507-celebration-series-music-minneapolis/
    rules = [Rule(LinkExtractor(allow=['/event/[0-9]+-.+/$']), 'parse_show')]

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'DOWNLOAD_DELAY': 1
    }

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('The Warming House', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'https://www.thewarminghouse.net'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'warminghouse.py'
        return discovery_section

    def parse_show(self, response):

        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        title_string = response.css('.event-info h1.headliners::text').extract_first()
        if title_string is not None:
            event_section.title = showspiderutils.kill_unicode_and_strip(title_string)
        else:
            return []

        # IGNORE OPEN MIC-LIKE EVENTS
        if re.search(
                r'open mic|uke jam|bluegrass jam|old time jam|rough draft songwriter night|song circle',
                title_string,
                re.IGNORECASE
        ):
            return []  # abort

        # age restriction
        # I think all shows are all ages, they don't serve liquor
        event_section.minimumAgeRestriction = 0

        # ticket prices
        price_text = response.css('.event-info .price-range::text').extract_first()
        if price_text is not None:
            prices = showspiderutils.check_text_for_prices(showspiderutils.kill_unicode_and_strip(price_text))
            if prices['doors'] is not None:
                event_section.ticketPriceDoors = prices['doors']
            if prices['advance'] is not None:
                event_section.ticketPriceAdvance = prices['advance']

        # sold out
        # could not find any sold out indicators

        # ticket purchase URL
        ticket_button_href = response.css('.event-info .ticket-price a::attr(href)').extract_first()
        if ticket_button_href is not None:
            event_section.ticketPurchaseUrl = ticket_button_href

        # parse doors date/time
        # datetime: 2018-09-20T18:00:00-05:00
        start_datetime = response.css('.event-info .times .start .value-title::attr(title)').extract_first()
        event_section.startDatetime = arrow.get(start_datetime)
        doors_string = response.css('.event-info .times .doors::text').extract_first()
        if doors_string is not None:
            doors_time_parts = doors_string.split(' ')[1].split(':')
            doors_ampm = doors_string.split(' ')[2]
            if doors_ampm is 'pm':
                doors_time_parts[0] = doors_time_parts[0] + 12
            doors = event_section.startDatetime.clone()
            event_section.doorsDatetime = doors.replace(hour=int(doors_time_parts[0]), minute=int(doors_time_parts[1]))

        # PERFORMERS SECTION
        # find performers
        # sometimes there's just one "performer" and its actually a description of a generic event
        # like "open mic night"
        performers = response.css('.artist-boxes .artist-box-headliner')
        performances = []
        for i, performer in enumerate(performers):
            # There is typically just one artist per section
            # TODO but occasionally a bunch are in one section like "band 1 // band 2 // band3"
            performance_section = PerformanceSection()

            performer_string = performer.css('.artist-headline .artist-name::text').extract_first()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer_string)

            performer_urls = performer.css('ul li a::attr(href)').extract()
            hrefs = []
            detected_fake_performance = False
            for i, href in enumerate(performer_urls):
                if re.search(r'http', href, re.IGNORECASE):
                    hrefs.append(href)
                if re.search(r'thewarminghouse.net', href, re.IGNORECASE):
                    detected_fake_performance = True
            if len(hrefs) > 0:
                performance_section.urls = hrefs

            performance_section.order = i

            if detected_fake_performance is not True:
                performances.append(performance_section)


        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
