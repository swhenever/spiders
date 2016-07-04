import scrapy
from scrapy.selector import Selector
from scrapy import log
import arrow
import dateutil
import re
from showoff_scrape.items import *

class IcehouseSpider(scrapy.Spider):

    name = 'icehouse'
    allowed_domains = ['icehousempls.com']
    start_urls = ['http://www.icehousempls.com/events/']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Icehouse', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.icehousempls.com'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'icehouse.py'
        return discovery_section

    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse(self, response):
        eventSelectors = response.css('div.eventlist article.eventlist-event')
        for index, eventSelector in enumerate(eventSelectors):
            event_section = EventSection()
            # DISCOVERY SECTION
            discovery_section = self.make_discovery_section()
            discovery_section.foundUrl = response.url

            # VENUE SECTION
            venue_section = self.make_venue_section()

            # EVENT SECTION
            # date/time
            date_string = eventSelector.css('p.date time.eventlist-meta-date::text').extract()
            date_string = self.kill_unicode_and_strip(date_string[0])
            time_string = eventSelector.css('p.date span.eventlist-meta-time time.event-time-12hr::text').extract()
            time_string = self.kill_unicode_and_strip(time_string[0])
            event_date = arrow.get(time_string.strip() + " " + date_string.strip(), [r"h:mma \w+, MMMM +D, YYYY"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))  # 11:00pm Friday, July  8, 2016
            event_section.startDatetime = event_date

            # title / event url (and performers)
            title_selector = eventSelector.css('h1.entry-title')
            performers_text = title_selector.css('a::text').extract()  # MARK MALLMAN + RONiiA
            performers_text = self.kill_unicode_and_strip(performers_text[0])
            event_section.title = performers_text
            event_url = title_selector.css('a::attr(href)').extract()
            event_section.eventUrl = venue_section.venueUrl + event_url[0]

            # ticket price
            possible_price_strings = eventSelector.css('div.eventlist-excerpt h2::text').extract()
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
                performance_section.name = self.kill_unicode_and_strip(performer)
                performance_section.order = performer_index
                performances.append(performance_section)

            # MAKE HipLiveMusicShowBill
            showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

            # Make Scrapy ShowBill container item
            scrapy_showbill_item = ScrapyShowBillItem(showbill)
            yield scrapy_showbill_item
