from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import showspiderutils
import dateutil
from showoff_scrape.items import *


class HoneySpider(CrawlSpider):

    name = 'honey'
    allowed_domains = ['honeympls.com']
    start_urls = ['http://honeympls.com/events/category/live-music/']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    url_date_regex = showspiderutils.make_regex_for_matching_dates_in_urls(timezone)

    rules = [
        Rule(LinkExtractor(allow=['/event/.+']), 'parse_show'),
        Rule(LinkExtractor(allow=['/events/category/live-music/' + url_date_regex['year'] + '-' + url_date_regex['month'] + '/'])),
        Rule(LinkExtractor(allow=['/events/category/live-music/' + url_date_regex['nextyear_year'] + '-' + url_date_regex['nextyear_month'] + '/']))
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Honey', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://honeympls.com'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('honey.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url

        # date/time
        date_elem = response.css('.tribe-events-meta-group abbr.tribe-events-start-date')
        date_string = date_elem.xpath('@title').extract_first()  # YYYY-MM-DD
        # sometimes there is both start and end times in the time string
        time_strings = response.css('.tribe-events-meta-group .tribe-events-start-time::text').extract_first().split('-')
        if len(time_strings) > 1:
            end_string = showspiderutils.time_normalize(showspiderutils.kill_unicode_and_strip(time_strings[1]))
            event_section.endDatetime = arrow.get(end_string + " " + date_string, [r"h:mma YYYY-MM-DD"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        start_string = showspiderutils.time_normalize(showspiderutils.kill_unicode_and_strip(time_strings[0]))
        event_section.startDatetime = arrow.get(start_string + " " + date_string, [r"h:mma YYYY-MM-DD"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # title
        title_string = response.css('h1.tribe-events-single-event-title::text').extract_first()
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)

        # price
        prices_string = response.css('.tribe-events-meta-group .tribe-events-event-cost::text').extract_first()
        if prices_string:
            prices = showspiderutils.check_text_for_prices(prices_string)
            if prices['doors'] is not None:
                event_section.ticketPriceDoors = prices['doors']
            if prices['advance'] is not None:
                event_section.ticketPriceAdvance = prices['advance']

        # ticket purchase URL
        # Honey generally doesn't have advance tickets. Sometimes there is a URL in body text.
        # TODO Could search body for popular ticket site URLs: eventbrite, brownpapertickets, etc.

        # age restriction
        body_paragraphs = response.css('.tribe-events-single-event-description p::text').extract()
        for para_index, paragraph in enumerate(body_paragraphs):
            age_restriction = showspiderutils.check_text_for_age_restriction(paragraph)
            if age_restriction is not None:
                event_section.minimumAgeRestriction = age_restriction

        # performances
        # TODO: honey performers are really scattered in body text. Not sure how to extract them. Maybe check for URLs?
        performances = []

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        yield scrapy_showbill_item
