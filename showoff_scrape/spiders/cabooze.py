import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response
import showspiderutils


class CaboozeSpider(CrawlSpider):

    name = 'cabooze'
    allowed_domains = ['cabooze.com']
    start_urls = ['http://www.cabooze.com/']
    rules = [Rule(LinkExtractor(allow=['/event/\d+-.+']), 'parse_show')]  # /event/1209287-ne-obliviscaris-minneapolis/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('The Cabooze', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.cabooze.com'
        return venue_section

    def parse_show(self, response):
        #inspect_response(response, self)

        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('cabooze.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        name_result = response.css('div.event-info h1.headliners::text').extract()
        event_section.title = showspiderutils.kill_unicode_and_strip(name_result[0])

        # age restriction
        age_restriction_string = response.css('div.event-info h2.age-restriction::text').extract()
        if len(age_restriction_string) > 0:
            age_restriction_string = showspiderutils.kill_unicode_and_strip(age_restriction_string[0])
            event_section.minimumAgeRestriction = showspiderutils.check_text_for_age_restriction(age_restriction_string)

        # ticket prices
        # string is like: $7 - $10 or $20.00 - $50.00 or $10 Before 11:00PM / $15 After
        ticket_price_string = response.css('div.ticket-price h3.price-range::text').extract()
        ticket_price_string = showspiderutils.kill_unicode_and_strip(ticket_price_string[0])
        prices = re.findall(ur'[$]\d+(?:\.\d{2})?', ticket_price_string)
        if len(prices) == 2:
            event_section.ticketPriceAdvance = float(prices[0].strip('$'))
            event_section.ticketPriceDoors = float(prices[1].strip('$'))
        elif len(prices) == 1:
            event_section.ticketPriceDoors = float(prices[0].strip('$'))

        # sold out
        # Can not currently find a sold out example on cabooze site! Not sure what it looks like
        # sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        # if len(sold_out_selectors) > 0:
        #     event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('h3.ticket-link a.tickets::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = showspiderutils.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        date_string = response.css('div.event-info h2.dates::text').extract()  # Fri, July 15, 2016
        date_string = showspiderutils.kill_unicode_and_strip(date_string[0])

        doors_string = response.css('div.event-info h2.times span.doors::text').extract()  # Doors: 7:00 pm
        if len(doors_string) > 0:
            doors_string = showspiderutils.kill_unicode_and_strip(doors_string[0])
            doors_string = re.search(ur'\d+:\d+ [ap]m', doors_string).group(0)  # 7:00 pm
            doors_date = arrow.get(date_string + doors_string, [r"\w+, MMMM +D, YYYYh:mm a"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.doorsDatetime = doors_date

        start_string = response.css('div.event-info h2.times span.start::text').extract()  # Show: 8:00 pm
        start_string = showspiderutils.kill_unicode_and_strip(start_string[0])
        start_string = re.search(ur'\d+:\d+ [ap]m', start_string).group(0)  # 8:00 pm
        start_date = arrow.get(date_string + start_string, [r"\w+, MMMM +D, YYYYh:mm a"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.startDatetime = start_date

        # PERFORMERS SECTION
        # find performers
        performer_strings = [event_section.title]  # headliner artist is in title
        # supporting artists in supports container
        supporting_performer_strings = response.css('div.event-info h2.supports::text').extract()
        if len(supporting_performer_strings) > 0:
            supporting_performer_strings = showspiderutils.kill_unicode_and_strip(supporting_performer_strings[0])
            performer_strings = performer_strings + supporting_performer_strings.split(', ')

        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
