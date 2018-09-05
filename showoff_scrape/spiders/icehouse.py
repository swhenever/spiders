import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
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
    rules = [Rule(LinkExtractor(allow=['/events/\d+/\d+/\d+/.+']), 'parse_show')]

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

        # lots of meta content in h2 tags in body
        body_h2_strings = response.css('.eventitem-column-content h2::text').extract()

        # date/time
        # Some shows have a separate doors/showtime listing in body, some just have the header area start time
        # Check first for a doors/showtime listing
        start_time_string = doors_time_string = None
        for h2_string_index, h2_string_text in enumerate(body_h2_strings):
            # 3 groups in regex, so this returns a list of tuples
            times = re.findall(ur'(\d+(:\d\d)?[p|a]m\s(doors|show))', h2_string_text, re.IGNORECASE)
            if len(times) == 1:
                start_time_string = showspiderutils.time_normalize(showspiderutils.kill_unicode_and_strip(times[0][0]).replace(' doors', '').replace(' show', ''))
                doors_time_string = None
            elif len(times) == 2:
                # first is doors
                doors_time_string = showspiderutils.time_normalize(showspiderutils.kill_unicode_and_strip(times[0][0]).strip(' doors'))  # 10:30pm or 4pm
                # second is showtime, if present
                start_time_string = showspiderutils.time_normalize(showspiderutils.kill_unicode_and_strip(times[1][0]).strip(' show'))

        # fallback to header area start time if couldn't find the above
        if start_time_string is None:
            # actually looks like "10:30pm - 11:55pm" before JS kills the 2nd time value. 2nd time is not meaningful
            start_time_string = response.css('p.event-time time.event-time-12hr::text').extract()
            start_time_string = showspiderutils.kill_unicode_and_strip(start_time_string[0])
            times = re.findall(ur'\d+:\d\d[p|a]m', start_time_string, re.IGNORECASE)
            start_time_string = showspiderutils.time_normalize(times[0])

        date_string = response.css('p.event-time time.event-meta-heading::text').extract()
        date_string = showspiderutils.kill_unicode_and_strip(date_string[0])
        event_section.startDatetime = arrow.get(start_time_string.strip() + " " + date_string.strip(), [r"h:mma \w+, MMMM +D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))  # 11:00pm Friday, July  8, 2016
        if doors_time_string is not None:
            event_section.doorsDatetime = arrow.get(doors_time_string.strip() + " " + date_string.strip(), [r"h:mma \w+, MMMM +D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))  # 11:00pm Friday, July  8, 2016

        # title / event url (and performers)
        title_string = response.css('h1.page-title::text').extract()
        event_section.title = performers_combined_string = showspiderutils.kill_unicode_and_strip(title_string[0])
        event_section.eventUrl = response.url

        # ticket price
        for price_index, possible_price in enumerate(body_h2_strings):
            prices = showspiderutils.check_text_for_prices(possible_price)
            if prices['doors'] is not None:
                event_section.ticketPriceDoors = prices['doors']
            if prices['advance'] is not None:
                event_section.ticketPriceAdvance = prices['advance']

        # get ticket URLs. Have to check every A tag in the body for BUY TICKETS text :(
        possible_tickets = response.css('.eventitem-column-content a')
        possible_ticket_texts = possible_tickets.xpath('text()').extract()
        possible_ticket_urls = possible_tickets.xpath('@href').extract()
        for ticket_url_index, possible_ticket_url_text in enumerate(possible_ticket_texts):
            if re.search(ur'buy tickets', possible_ticket_url_text, re.IGNORECASE):
                event_section.ticketPurchaseUrl = possible_ticket_urls[ticket_url_index]

        # age restriction
        for age_index, possible_age_text in enumerate(body_h2_strings):
            minimum_age = showspiderutils.check_text_for_age_restriction(possible_age_text)
            if minimum_age is not None:
                event_section.minimumAgeRestriction = minimum_age

        # performances
        performances = []
        performer_strings = response.css('.eventitem-column-content h3::text').extract()
        for performer_index, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            # often a colon is at the end of the performer name
            if performance_section.name.endswith(":"):
                performance_section.name = performance_section.name[:-1]
            performance_section.order = performer_index
            performances.append(performance_section)

        if len(performances) == 0:
            # fallback to the performers combined string in the title
            performers = performers_combined_string.split(' + ')
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
