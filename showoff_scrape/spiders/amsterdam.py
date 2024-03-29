import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
import showspiderutils
from scrapy.shell import inspect_response

class AmsterdamSpider(CrawlSpider):

    name = 'amsterdam'
    allowed_domains = ['amsterdambarandhall.com']
    start_urls = ['http://www.amsterdambarandhall.com/events-new/']
    rules = [Rule(LinkExtractor(allow=['/events/.+/']), 'parse_show')]  # /events/devils-flying-machine-faun-and-a-pan-flute-atl-surprise-party/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Amsterdam Bar and Hall', 'Saint Paul', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.amsterdambarandhall.com'
        return venue_section

    def make_discovery_section(self):
        discovery_section = showspiderutils.make_discovery_section('amsterdam.py')
        return discovery_section

    def parse_title_artists(self, title):
        artist_strings = []

        # get rid of "special guests"
        title = re.sub(r'special guests', r'', title, 0, re.IGNORECASE)

        if re.search(r',\W', title, re.IGNORECASE):  # doesn't seem like amsterdam uses and or & in title band lists
            artist_strings += map(lambda p: showspiderutils.kill_unicode_and_strip(p), re.split(r'\W&\W|\Wand\W|,\W', title))
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
        name_result = response.css('header.entry-header h2::text').extract()
        event_section.title = showspiderutils.kill_unicode_and_strip(name_result[0])

        # Get metadata from first paragraph, separated by "X" images (replace those with spaces so strings are separate)
        metadata_string = response.css('div.entry-content p::text').extract_first()
        metadata_string = showspiderutils.kill_unicode_and_strip(metadata_string, ' ')

        # age restriction
        if re.search(r'all ages|aa', metadata_string, re.IGNORECASE):
            event_section.minimumAgeRestriction = 0
        elif re.search(r'\d\d\+', metadata_string, re.IGNORECASE):
            event_section.minimumAgeRestriction = int(re.search(r'\d\d\+', metadata_string, re.IGNORECASE).group().strip('+'))

        # ticket prices
        # string is like: $18 Advance / $20 Day of show
        prices = showspiderutils.check_text_for_prices(metadata_string)
        if prices['doors'] is not None:
            event_section.ticketPriceDoors = prices['doors']
        if prices['advance'] is not None:
            event_section.ticketPriceAdvance = prices['advance']

        # sold out
        # don't see a sold out show on Amsterdam calendar, so not sure what one looks like! TODO
        # sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        # if len(sold_out_selectors) > 0:
        #     event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('h3.ticket-link a.tickets::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = showspiderutils.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        date_string = response.css('header.entry-header h4::text').extract_first()  # Wednesday, August 3
        date_string = showspiderutils.kill_unicode_and_strip(date_string)
        year_string = arrow.utcnow().format('YYYY')
        times = showspiderutils.check_text_for_times(metadata_string)
        if len(times) > 1:
            event_section.doorsDatetime = arrow.get(date_string + " " + times[0] + year_string, [r"\w+, MMMM D h:mmaYYYY"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = arrow.get(date_string + " " + times[1] + year_string, [r"\w+, MMMM D h:mmaYYYY"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
        elif len(times) == 1:
            event_section.startDatetime = arrow.get(date_string + " " + times[0] + year_string, [r"\w+, MMMM D h:mmaYYYY"]).replace(tzinfo=dateutil.tz.gettz(self.timezone))
        else:
            # If we can't find any times, ShowBill would be incomplete.
            # @todo some way of logging this perhaps
            return []

        # PERFORMERS SECTION
        # find performers from title
        performerStrings = self.parse_title_artists(event_section.title)

        # some pages do actually use on-page elements to dsecribe individual artists (ex: http://www.amsterdambarandhall.com/events/scarlet-sails-nina-diaz/)
        # @todo implement parsing of page content artist elements 

        performances = []
        for i, performer in enumerate(performerStrings):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
