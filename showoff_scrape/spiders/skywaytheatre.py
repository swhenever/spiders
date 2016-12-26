from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import datetime
import showspiderutils
import dateutil
from showoff_scrape.items import *


class SkywayTheatreSpider(CrawlSpider):

    name = 'skywaytheatre'
    allowed_domains = ['skywaytheatre.com']
    start_urls = ['http://www.skywaytheatre.com/calendar']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    url_date_regex = showspiderutils.make_regex_for_matching_dates_in_urls(timezone)

    rules = [
        Rule(LinkExtractor(allow=['/event/.+']), 'parse_show'),
        Rule(LinkExtractor(allow=['/calendar/month/' + url_date_regex['year'] + '-' + url_date_regex['month']])),
        Rule(LinkExtractor(allow=['/calendar/month/' + url_date_regex['nextyear_year'] + '-' + url_date_regex['nextyear_month']]))
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Skyway Theatre', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.skywaytheatre.com'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('skywaytheatre.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url

        # Most info is in body paragraphs
        body_paragraphs = response.css('.main-content .field-name-body .field-item p::text').extract()

        # date/time
        # get date string
        date_string = False
        for para_index, paragraph in enumerate(body_paragraphs):
            possible_date = showspiderutils.check_text_is_date(paragraph)
            if isinstance(possible_date, datetime.datetime):
                date_string = str(possible_date.year) + "-" + str(possible_date.month) + "-" + str(possible_date.day)

        if date_string is False:
            return []  # abort: we could not determine the date, so no event can be parsed

        # get time string and assign show times
        times = []
        for para_index, paragraph in enumerate(body_paragraphs):
            times += showspiderutils.check_text_for_times(paragraph, True)
        times = list(set(times))  # remove duplicates
        if len(times) == 1:
            event_section.startDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        elif len(times) == 2:
            event_section.doorsDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = arrow.get(times[1] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # title and stage
        title_stage_string = response.css('.main-content h2.node-title::text').extract_first()
        title_stage_parts = showspiderutils.kill_unicode_and_strip(title_stage_string).split(' - ')
        event_section.title = title_stage_parts[0]
        if len(title_stage_parts) > 1:
            stage = title_stage_parts[1]
        else:
            stage = False

        # price
        prices = []
        final_prices = None
        for para_index, paragraph in enumerate(body_paragraphs):
            possible_prices = showspiderutils.check_text_for_prices(paragraph)
            if possible_prices['doors'] is not None and possible_prices['advance'] is not None:
                # wow, both prices in one paragraph
                final_prices = possible_prices
            else:
                # just 'doors' will be entered
                prices.append(possible_prices['doors'])
        prices = sorted(list(set(prices)))  # remove duplicates and sort ascending by price
        if final_prices is not None:
            event_section.ticketPriceAdvance = final_prices['advance']
            event_section.ticketPriceDoors = final_prices['doors']
        elif len(prices) == 1:
            event_section.ticketPriceDoors = prices[0]
        elif len(prices) > 1:
            event_section.ticketPriceAdvance = prices[0]
            event_section.ticketPriceDoors = prices[1]
            # todo: handle VIP packages etc.

        # ticket purchase URL
        event_section.ticketPurchaseUrl = response.css('.main-content .buy-tickets a::attr(href)').extract_first()

        # age restriction
        age_restriction = None
        for para_index, paragraph in enumerate(body_paragraphs):
            age_restriction = showspiderutils.check_text_for_age_restriction(paragraph)
        if age_restriction is not None:
            event_section.minimumAgeRestriction = age_restriction

        # performances
        # TODO: skyway performers are really scattered in body
        # probably search soundcloud / mixcloud / facebook URLs
        performances = []

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        return scrapy_showbill_item
