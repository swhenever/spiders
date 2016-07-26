import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class MillCitySpider(CrawlSpider):

    name = 'millcitynights'
    allowed_domains = ['millcitynights.com']
    start_urls = ['http://www.millcitynights.com/events']
    rules = [Rule(LinkExtractor(allow=['/events/detail/\d+']), 'parse_show')]  # /events/detail/311702

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Mill City Nights', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.millcitynights.com'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'millcitynights.py'
        return discovery_section

    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse_subtitle_artists(self, title):
        artist_strings = []

        # get rid of "with "
        title = re.sub(r'with\W', r'', title, 0, re.IGNORECASE)

        if re.search(r'\W&\W|\Wand\W|,\W', title, re.IGNORECASE):  # doesn't seem like amsterdam uses and or & in title band lists
            artist_strings += map(lambda p: self.kill_unicode_and_strip(p), re.split(r'\W&\W|\Wand\W|,\W', title))
        else:
            artist_strings.append(title)

        return artist_strings

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
        name_result = response.css('div.event_detail h1::text').extract_first()
        event_section.title = self.kill_unicode_and_strip(name_result)

        # age restriction
        age_string = self.kill_unicode_and_strip(response.css('div.event_detail div.age_res::text').extract_first())
        ages = re.findall(ur'(\d\d|all ages)', age_string, re.IGNORECASE)
        if len(ages) > 0 and ages[0] == 'all ages':
            event_section.minimumAgeRestriction = 0
        elif len(ages) > 0:
            event_section.minimumAgeRestriction = ages[0].strip()

        # ticket prices
        # string is like: $18 Advance / $20 Day of show
        ticket_price_string = response.css('div.event_detail div.description div.collapse-wrapper p::text').extract()
        ticket_price_string = ''.join(ticket_price_string)  # put all P text into one string
        ticket_price_string = self.kill_unicode_and_strip(ticket_price_string)
        prices = re.findall(ur'[$]\d+(?:\.\d{2})?', ticket_price_string, re.IGNORECASE)
        if len(prices) > 1:
            event_section.ticketPriceAdvance = float(prices[0].strip('$'))
            event_section.ticketPriceDoors = float(prices[1].strip('$'))
        elif len(prices) == 1:
            event_section.ticketPriceDoors = float(prices[0].strip('$'))

        # sold out
        # Not seeing any "sold out" shows on Mill City Nights calendar, so not sure what this looks like!
        # sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        # if len(sold_out_selectors) > 0:
        #     event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('div.event_detail a.btn-tickets::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = self.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        date_string = ''.join(response.css('div.event_detail li.date::text').extract())  # WED, AUGUST 3, 2016
        date_string = self.kill_unicode_and_strip(date_string)

        doors_string = ''.join(response.css('div.event_detail ul.details li span.doors label::text').extract())  # Doors7:00 PM
        doors_string = self.kill_unicode_and_strip(doors_string)
        doors_string = re.search(ur'\d+:\d+ [ap]m', doors_string, re.IGNORECASE).group(0)  # 7:30 PM

        start_string = response.css('div.event_detail ul.details li span.text-large::text').extract_first()  # 8:00 PM
        start_string = self.kill_unicode_and_strip(start_string)

        doors_date = arrow.get(date_string + doors_string, [r"\w+, MMMM +D, YYYYh:mm a"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.doorsDatetime = doors_date
        start_date = arrow.get(date_string + start_string, [r"\w+, MMMM +D, YYYYh:mm a"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.startDatetime = start_date

        # PERFORMERS SECTION
        # find performers
        performer_strings = [event_section.title]  # title is usually the first performer
        subtitle_string = response.css('div.event_detail div.page_header_left h4::text').extract_first()
        if subtitle_string:
            performer_strings += self.parse_subtitle_artists(self.kill_unicode_and_strip(subtitle_string))
        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = self.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
