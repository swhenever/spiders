import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
import arrow
import dateutil
from bs4 import BeautifulSoup
import re
import showspiderutils
from showoff_scrape.items import *

class DakotaJazzClub(CrawlSpider):

    name = 'dakotajazzclub'
    allowed_domains = ['www.dakotacooks.com']
    start_urls = ['http://www.dakotacooks.com/calendar/']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    url_date_regex = showspiderutils.make_regex_for_matching_dates_in_urls(timezone, month_format='M')

    # http://www.dakotacooks.com/calendar/2018-02/
    rules = [
        Rule(LinkExtractor(allow=['/event/[a-zA-Z0-9\-_]+/$']), 'parse_show'),
        Rule(LinkExtractor(allow=['/calendar/' + url_date_regex['year'] + '-' + url_date_regex['month'] + '/'])),
        Rule(LinkExtractor(allow=['/calendar/' + url_date_regex['nextyear_year'] + '-' + url_date_regex['nextyear_month'] + '/']))
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Dakota Jazz Club', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.dakotacooks.com'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('dakotajazzclub.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()

        # url
        event_section.eventUrl = response.url

        # title
        title_string = response.css('#tribe-events-content > h2::text').extract_first()
        # check if this event has sold out
        if re.search(r'sold out', title_string, re.IGNORECASE):
            event_section.soldOut = True
            title_string = re.sub(r'sold out:|sold out', '', title_string, 0, re.IGNORECASE) # remove text from title
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)  

        # get event meta text, have to search for time in here
        meta_soup = BeautifulSoup(response.css('#tribe-events-content .module.third').extract_first(), "lxml")
        meta_text = meta_soup.get_text().strip()

        # date
        date_string = response.css('#tribe-events-content meta[itemprop=startDate]::attr(content)').extract_first() # Friday, Jan 26, 2018
        # time
        times = showspiderutils.check_text_for_times(meta_text)
        if len(times) > 0:
            event_section.startDatetime = arrow.get(times[0] + " " + date_string, [r"h:mma dddd, MMM D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        else:
            return [] # failed to parse a time, so we can't succeed with a showbill

        # age restriction
        # dakota is a bar, so we're assuming 21+
        event_section.minimumAgeRestriction = 21

        # price
        # ticket price is formatting $25 or $60-55-50-40, price based on quality of seat, so
        # TODO support multiple ticket tiers
        # shows are either advance ticketed (Ticketed) or at the door (Cover) based on a random link in meta text :(
        price_strings = re.findall(ur'[$][\d-]+', meta_text)
        if len(price_strings) is 0:
            price_strings = re.findall(ur'\d\d-[\d-]+', meta_text) # try without $ prefix, instead ##- prefix
        if len(price_strings) > 0:
            prices = price_strings[0].split('-')
            prices = [price.strip('$ ') for price in prices]
            low_price = None
            for price_index, price in enumerate(prices):
                if low_price is None or int(price) < low_price:
                    low_price = int(price)
            if low_price is not None:
                # try to find the link that says either Cover or Ticketed
                if len(meta_soup.find_all("a", string="Cover")) > 0:
                    event_section.ticketPriceDoors = low_price
                if len(meta_soup.find_all("a", string="Ticketed")) > 0:
                    event_section.ticketPriceAdvance = low_price

        # ticket url
        url_string = response.css('#tribe-events-content .module.third a.button.gold::attr(href)').extract_first()
        if url_string is not None:
            event_section.ticketPurchaseUrl = url_string

        # PERFORMANCES
        performances = []
        # if there is more than one description paragraph, then first one is addtl performers
        for index, performer in enumerate(response.css('#tribe-events-content .module.first h3::text').extract()):
            performance_section = PerformanceSection()
            performance_section.name = re.sub(r'^about', '', performer, 0, re.IGNORECASE).strip()
            performance_section.order = index
            performances.append(performance_section)
        
        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)
        return scrapy_showbill_item
