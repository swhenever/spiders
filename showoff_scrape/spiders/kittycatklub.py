import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
import arrow
import dateutil
from bs4 import BeautifulSoup
import showspiderutils
from showoff_scrape.items import *

class KittyCatKlubSpider(CrawlSpider):

    name = 'kittycatklub'
    allowed_domains = ['www.kittycatklub.net']
    start_urls = ['https://www.kittycatklub.net/music/']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    url_date_regex = showspiderutils.make_regex_for_matching_dates_in_urls(timezone, month_format='M')

    rules = [
        Rule(LinkExtractor(allow=['/music/' + url_date_regex['year'] + '/' + url_date_regex['month'] + '/\d+/[a-zA-Z0-9\-_]+$']), 'parse_show'),
        Rule(LinkExtractor(allow=['/music/' + url_date_regex['nextyear_year'] + '/' + url_date_regex['nextyear_month'] + '/\d+/[a-zA-Z0-9\-_]+$']), 'parse_show')
    ]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Kitty Cat Klub', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.kittycatklub.net'
        return venue_section

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('kittycatklub.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()

        # url
        event_section.eventUrl = response.url

        # title
        title_string = response.css('.eventitem .eventitem-title::text').extract_first()
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)  

        # date
        date_string = response.css('.eventitem time.event-date::attr(datetime)').extract_first() # YYYY-MM-DD
        # time
        time_string = response.css('.eventitem time.event-time-12hr::text').extract_first() # H:MM PM

        event_section.startDatetime = arrow.get(time_string + " " + date_string, [r"h:mm a YYYY-MM-DD"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # description text
        description_soup = BeautifulSoup(response.css('.eventitem .eventitem-column-content').extract_first(), "lxml")
        description_text = description_soup.get_text().strip()

        # age restriction
        age_restriction = showspiderutils.check_text_for_age_restriction(description_text)
        if age_restriction is None:
            event_section.minimumAgeRestriction = 21 # assume 21+ as default, it's a bar
        else:
            event_section.minimumAgeRestriction = age_restriction

        # price
        prices = showspiderutils.check_text_for_prices(description_text)
        if prices['doors'] is not None:
            event_section.ticketPriceDoors = prices['doors']

        # N/A ticket url
        # Kitty Cat Klub does not offer advance tickets

        # PERFORMANCES
        performances = []
        performer_strings = [event_section.title] # first performer is the title
        # if there is more than one description paragraph, then first one is addtl performers
        if len(response.css('.eventitem .eventitem-column-content p').extract()) > 1:
            addtl_performers_string = response.css('.eventitem .eventitem-column-content p::text').extract_first()
            addtl_performers = showspiderutils.parse_text_for_performers(addtl_performers_string)
            if len(addtl_performers) > 0:
                performer_strings.extend(addtl_performers)
        
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
