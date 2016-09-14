import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.selector import Selector
import arrow
import showspiderutils
import dateutil
import re
from showoff_scrape.items import *


class IcehouseSpider(CrawlSpider):

    name = 'icehouse'
    allowed_domains = ['icehousempls.com']
    start_urls = ['http://www.icehousempls.com/events/']

    # ex: http://www.icehousempls.com/events/2016/9/17/sophia-eris-album-release-saint-laron-gym-kang-ness-nite
    rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/\d+/.+']), 'parse_show')]

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Icehouse', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.icehousempls.com'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('icehouse.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()

        # date/time
        # Some shows have a separate doors/showtime listing in body, some just have the header area start time
        # Check first for a doors/showtime listing
        body_h2_strings = response.css('.eventitem-column-content h2::text').extract()
        start_time_string = doors_time_string = None
        for h2_string_index, h2_string_text in enumerate(body_h2_strings):
            # 3 groups in regex, so this returns a list of tuples
            times = re.findall(ur'(\d+(:\d\d)?[p|a]m\s(doors|show))', h2_string_text, re.IGNORECASE)
            if len(times) == 1:
                start_time_string = showspiderutils.kill_unicode_and_strip(times[0][0]).replace(' doors', '').replace(' show', '')
                doors_time_string = None
            elif len(times) == 2:
                # first is doors
                doors_time_string = showspiderutils.kill_unicode_and_strip(times[0][0]).strip(' doors')  # 10:30pm or 4pm
                # second is showtime, if present
                start_time_string = showspiderutils.kill_unicode_and_strip(times[1][0]).strip(' show')

        # fallback to header area start time if couldn't find the above
        if start_time_string is None:
            # actually looks like "10:30pm - 11:55pm" before JS kills the 2nd time value. 2nd time is not meaningful
            start_time_string = response.css('p.event-time time.event-time-12hr::text').extract()
            start_time_string = showspiderutils.kill_unicode_and_strip(start_time_string)
            times = re.findall(ur'\d+:\d\d[p|a]m', start_time_string, re.IGNORECASE)
            start_time_string = times[0]

        # handle if time is "4pm" instead of "4:00pm"
        # @todo

        date_string = response.css('p.event-time time.event-meta-heading::text').extract()
        date_string = showspiderutils.kill_unicode_and_strip(date_string[0])
        event_section.startDatetime = arrow.get(start_time_string.strip() + " " + date_string.strip(), [r"h:mma \w+, MMMM +D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))  # 11:00pm Friday, July  8, 2016
        if doors_time_string is not None:
            event_section.endDatetime = arrow.get(doors_time_string.strip() + " " + date_string.strip(), [r"h:mma \w+, MMMM +D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))  # 11:00pm Friday, July  8, 2016

        # @todo START HERE
        # title / event url (and performers)
        title_selector = response.css('h1.entry-title')
        performers_text = title_selector.css('a::text').extract()  # MARK MALLMAN + RONiiA
        performers_text = showspiderutils.kill_unicode_and_strip(performers_text[0])
        event_section.title = performers_text
        event_url = title_selector.css('a::attr(href)').extract()
        event_section.eventUrl = venue_section.venueUrl + event_url[0]

        # ticket price
        possible_price_strings = response.css('div.eventlist-excerpt h2::text').extract()
        for price_index, possible_price in enumerate(possible_price_strings):
            if re.search('no cover', possible_price, re.IGNORECASE):
                event_section.ticketPriceDoors = 0
            elif re.search('at the door', possible_price, re.IGNORECASE):
                prices = re.findall(ur'[$]\d+(?:\.\d{2})?', possible_price)
                if len(prices) == 2:
                    event_section.ticketPriceAdvance = float(prices[0].strip('$'))
                    event_section.ticketPriceDoors = float(prices[1].strip('$'))
                elif len(prices) == 1:
                    event_section.ticketPriceDoors = float(prices[0].strip('$'))

        # @todo: ticket URL. Would need to change to a multiple level spider, because this is in the event page

        # performances
        performances = []
        performers = performers_text.split(' + ')
        for performer_index, performer in enumerate(performers):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            performance_section.order = performer_index
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        yield scrapy_showbill_item
