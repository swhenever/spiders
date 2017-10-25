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

        # date/time
        # get date string
        date_string = False
        possible_date = showspiderutils.check_text_is_date(response.css('.tribe-events-single .tribe_events h2::text').extract_first())
        if isinstance(possible_date, datetime.datetime):
            date_string = str(possible_date.year) + "-" + str(possible_date.month) + "-" + str(possible_date.day)

        if date_string is False:
            return []  # abort: we could not determine the date, so no event can be parsed

        # get time string and assign show times
        time_string = response.css('.tribe-events-single .event-start-times::text').extract_first()
        times = []
        times += showspiderutils.check_text_for_times(time_string)
        times = list(set(times))  # remove duplicates
        if len(times) == 1 and re.search(ur'door', time_string, re.IGNORECASE): 
            event_section.doorsDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        elif len(times) == 1:
            event_section.startDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        elif len(times) == 2:
            event_section.doorsDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = arrow.get(times[1] + " " + date_string, [r"h:mma YYYY-M-D"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # title
        title_string = response.css('.tribe-events-single-event-title::text').extract_first()
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)

        # stage
        stage_string = response.css('.single-e-venue::text').extract_first()
        stage_string = showspiderutils.kill_unicode_and_strip(stage_string)
        if len(stage_string) > 0 and stage_string.lower() != 'skyway theatre':
            stage = stage_string
        else:
            stage = False

        # price
        prices = []
        final_prices = None
        price_string = response.css('.single-ticket-row h5::text').extract_first();
        possible_prices = showspiderutils.check_text_for_prices(price_string)
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
            event_section.ticketPriceAdvance = prices[0]
        elif len(prices) > 1:
            event_section.ticketPriceAdvance = prices[0]
            event_section.ticketPriceDoors = prices[1]
            # todo: handle VIP packages etc.

        # ticket purchase URL
        event_section.ticketPurchaseUrl = response.css('.single-ticket-row a::attr(href)').extract_first()

        # age restriction
        age_restriction = None
        age_elements = response.css('.tribe-events-single pre::text').extract()
        if len(age_elements) == 0:
            # see if there is any sub element under the pre, like <strong>
            age_elements = response.css('.tribe-events-single pre *::text').extract()
        for para_index, paragraph in enumerate(age_elements):
            age_restriction = showspiderutils.check_text_for_age_restriction(paragraph)
        if age_restriction is not None:
            event_section.minimumAgeRestriction = age_restriction

        # performances
        performances = []
        performer_strings = response.css('.event-artists h3::text').extract()
        for performer_index, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            performance_section.order = performer_index
            if stage is not False:
                performance_section.stage = stage
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        return scrapy_showbill_item
