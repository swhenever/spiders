from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import datetime
from bs4 import BeautifulSoup
import showspiderutils
import dateutil
from showoff_scrape.items import *


class HookAndLadderSpider(CrawlSpider):

    name = 'hookandladder'
    allowed_domains = ['thehookmpls.com']
    start_urls = ['http://thehookmpls.com/events/list/']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    rules = [
        Rule(LinkExtractor(allow=['/event/.+/']), 'parse_show'),
        Rule(LinkExtractor(allow=['/events/list/?tribe_event_display=list&tribe_paged=[2-9]']))
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Hook and Ladder', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://thehookmpls.com'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('hookandladder.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()

        # url
        event_section.eventUrl = response.url

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
        # get the event description and search for age info
        description_soup = BeautifulSoup(response.css('.tribe-events-single-event-description').extract_first(), "lxml")
        description_text = description_soup.get_text().strip()
        age_restriction = showspiderutils.check_text_for_age_restriction(description_text)
        if age_restriction is not None:
            event_section.minimumAgeRestriction = age_restriction

        # price
        cost_string = response.css('.tribe-events-event-cost::text').extract_first()
        if cost_string is None:
            # if cost is missing, its because show is free
            event_section.ticketPriceDoors = 0
        else:
            # price usually in $10/13 format
            if re.search(r'\$[0-9]+/[0-9]+', cost_string, re.IGNORECASE):
                cost_string = cost_string.strip('$ ')
                costs = cost_string.split('/')
                event_section.ticketPriceAdvance = costs[0]
                event_section.ticketPriceDoors = costs[1]
            else:
                #just try searching it for cost strings
                prices = showspiderutils.check_text_for_prices(cost_string)
                if prices['doors'] is not None:
                    event_section.ticketPriceDoors = prices['doors']
                if prices['advance'] is not None:
                    event_section.ticketPriceDoors = prices['advance']

        # ticket url
        # ticket button is also in the body
        buttons = description_soup.find_all("a", class_="btn")
        for index, button in enumerate(buttons):
            if button.get_text().strip() == 'BUY TICKETS':
                event_section.ticketPurchaseUrl = button['href']
        

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

