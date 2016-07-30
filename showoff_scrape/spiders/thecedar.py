import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class CedarSpider(CrawlSpider):

    name = 'thecedar'
    allowed_domains = ['thecedar.org']
    start_urls = ['http://www.thecedar.org/listing/']
    rules = [Rule(LinkExtractor(allow=['/event/\d+-.+']), 'parse_show')] #/event/829471-denim-matriarch-minneapolis/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('The Cedar', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.thecedar.org'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'thecedar.py'
        return discovery_section


    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse_show(self, response):
        #inspect_response(response, self)

        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        name_result = response.css('div.event-info h1.headliners::text').extract()
        event_section.title = self.kill_unicode_and_strip(name_result[0])

        # age restriction
        event_section.minimumAgeRestriction = 0  # Cedar shows are all all-ages

        # ticket prices
        # string is like: $18 Advance / $20 Day of show
        ticket_price_string = response.css('div.ticket-price h3.price-range::text').extract()
        ticket_price_string = self.kill_unicode_and_strip(ticket_price_string[0])
        prices = re.findall(ur'[$]\d+(?:\.\d{2})?', ticket_price_string)
        if len(prices) == 2:
            event_section.ticketPriceAdvance = float(prices[0].strip('$'))
            event_section.ticketPriceDoors = float(prices[1].strip('$'))
        elif len(prices) == 1:
            event_section.ticketPriceDoors = float(prices[0].strip('$'))

        # sold out
        sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        if len(sold_out_selectors) > 0:
            event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('h3.ticket-link a.tickets::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = self.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        doors_string = response.css('div.event-info h2.times span.doors::text').extract()  # Doors: 7:00 pm
        doors_string = self.kill_unicode_and_strip(doors_string[0])
        doors_string = re.search(ur'\d+:\d+ [ap]m', doors_string).group(0)  # 7:00 pm
        start_string = response.css('div.event-info h2.times span.start::text').extract()  # Show: 8:00 pm
        start_string = self.kill_unicode_and_strip(start_string[0])
        start_string = re.search(ur'\d+:\d+ [ap]m', start_string).group(0)  # 8:00 pm
        date_string = response.css('div.event-info h2.dates::text').extract()  # Fri, July 15, 2016
        date_string = self.kill_unicode_and_strip(date_string[0])

        doors_date = arrow.get(date_string + doors_string, [r"\w+, MMMM +D, YYYYh:mm a"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.doorsDatetime = doors_date
        start_date = arrow.get(date_string + start_string, [r"\w+, MMMM +D, YYYYh:mm a"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.startDatetime = start_date

        # PERFORMERS SECTION
        # find performers
        performerStrings = response.css('div.artist-boxes div.artist-headline span.artist-name::text').extract()
        performances = []
        for i, performer in enumerate(performerStrings):
            performance_section = PerformanceSection()
            performance_section.name = self.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
