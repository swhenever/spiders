import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class VarsitySpider(CrawlSpider):

    name = 'varsitytheater'
    allowed_domains = ['varsitytheater.org']
    start_urls = ['http://varsitytheater.org/shows-calendar-varsity-theater/']
    rules = [Rule(LinkExtractor(allow=['/events/.+/ ']), 'parse_show')]  # /events/warpaint/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Varsity Theater', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://varsitytheater.org'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'varsitytheater.py'
        return discovery_section


    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    # Return correct arrow time matching pattern for the given time string
    def make_arrow_time_pattern(self, time):
        if re.search(r':', time):
            time_pattern = 'h:mma'
        else:
            time_pattern = 'ha'
        return time_pattern

    # Process a string that may contain performers and return array of performers
    def process_performers_string(self, performers_string, force_split=False):
        # get rid of "blahblah presents" or "Presented by blah blah"
        performers_string = re.sub(r'^.+\Wpresents\W|\Wpresented by.+$', r'', performers_string, 0, re.IGNORECASE)

        # if we are forcing a split, or find text that indicates to  us a comma-separated list
        if force_split or re.search(r'with special guests|featuring', performers_string, re.IGNORECASE):
            # get rid of the unnecessary text
            performers_string = re.sub(r'^.+\Wwith special guests\W|^.+?\W?featuring\W', r'', performers_string, 0, re.IGNORECASE)
            performers = re.split(r', |, AND | AND |AND ', performers_string)
            performers = filter(None, performers)  # eliminate empty strings
            performers = map(lambda p: self.kill_unicode_and_strip(p), performers) # sanitize/strip each value
        else:
            performers = [self.kill_unicode_and_strip(performers_string)]
        return performers

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
        name_result = response.css('article.cpt_events h1.entry-title::text').extract()
        event_section.title = self.kill_unicode_and_strip(name_result[0])

        # Most properties are in a set of LIs
        property_text_strings = response.css('article.cpt_events ul.album-meta li::text').extract()
        date_string = self.kill_unicode_and_strip(property_text_strings[0])  # 22 - Jul - 2016
        ticket_price_string = self.kill_unicode_and_strip(property_text_strings[1])  # $20 Advance / $25 Day Of Show
        time_ages_string = self.kill_unicode_and_strip(property_text_strings[2])  # 7pm Doors - 8pm Music - 16+ with I.D.

        # ticket prices
        # string is like: $18 Advance / $20 Day of show
        prices = re.findall(ur'[$]\d+(?:\.\d{2})?', ticket_price_string)
        if len(prices) == 2:
            event_section.ticketPriceAdvance = float(prices[0].strip('$'))
            event_section.ticketPriceDoors = float(prices[1].strip('$'))
        elif len(prices) == 1:
            event_section.ticketPriceDoors = float(prices[0].strip('$'))

        # sold out
        sold_out_selectors = response.css('article.cpt_events ul.album-meta a.sold::text').extract()
        if len(sold_out_selectors) > 0:
            event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('article.cpt_events ul.album-meta a.buy::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = self.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # age restriction
        # TODO START HERE - age restriction is in time_ages_string - "7pm Doors - 8pm Music - 18+ with I.D."

        ages = re.findall(ur'(\d+\+|All Ages)', time_ages_string)
        if len(ages) > 0 and ages[0] == 'All Ages':
            event_section.minimumAgeRestriction = 0
        elif len(ages) > 0:
            event_section.minimumAgeRestriction = ages[0].strip(' +')

        # parse doors date/time
        # 22 - Jul - 20167pm
        times = re.findall(ur'\d?\d[ap]m|\d?\d:\d{2}[ap]m', time_ages_string)
        if len(times) > 1:
            doors_date = arrow.get(date_string + times[0], [r"DD - MMM - YYYY" + self.make_arrow_time_pattern(times[0])], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.doorsDatetime = doors_date
            start_date = arrow.get(date_string + times[1], [r"DD - MMM - YYYY" + self.make_arrow_time_pattern(times[1])], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = start_date
        else:
            start_date = arrow.get(date_string + times[0], [r"DD - MMM - YYYY" + self.make_arrow_time_pattern(times[0])], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = start_date

        # PERFORMERS SECTION
        # find performers
        headline_string_raw = response.css('article.cpt_events h1.entry-title::text').extract()

        # this sometimes has an unicode em dash in it. If so, split string by that
        # we're using a stupid hack to accomplish this (zap all unicode into an ascii placeholder)
        headline_string_raw = re.sub(r'[^\x00-\x7f]', r'|+|', headline_string_raw[0])
        performer_name_strings = headline_string_raw.split('|+|')

        # add any special guests to the list of performer names
        guest_string_raw = response.css('article.cpt_events p:last::text').extract()
        if len(guest_string_raw) > 0:
            guest_string = self.kill_unicode_and_strip(guest_string_raw[0])
            if not re.search(r'TBA', guest_string, re.IGNORECASE):
                guest_performances = self.process_performers_string(guest_string)
                performer_name_strings = performer_name_strings + guest_performances

        performances = []
        for i, performer in enumerate(performer_name_strings):
            performance_section = PerformanceSection()
            performance_section.name = performer
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
