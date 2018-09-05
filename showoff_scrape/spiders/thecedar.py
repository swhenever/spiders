import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import re
from bs4 import BeautifulSoup
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response
import showspiderutils

class CedarSpider(CrawlSpider):

    name = 'thecedar'
    allowed_domains = ['thecedar.org']
    start_urls = ['https://www.thecedar.org/listing/']
    rules = [Rule(LinkExtractor(allow=['/listing/\d+/\d+/\d+/[A-Za-z1-9-_]+$']), 'parse_show')] #/listing/2018/9/9/juana-molina-with-special-guest

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
        title_string = response.css('.eventitem .eventitem-title::text').extract_first()
        event_section.title = showspiderutils.kill_unicode_and_strip(title_string)

        # description text
        intro_description_soup = BeautifulSoup(response.css('.eventitem .eventitem-column-content .sqs-block-html').extract_first(), "lxml")
        intro_description = intro_description_soup.get_text().strip()

        # cancelled?
        if showspiderutils.check_text_for_cancelled(title_string):
            event_section.isCancelled = True

        # age restriction
        age_restriction = showspiderutils.check_text_for_age_restriction(intro_description)
        if age_restriction is None:
            event_section.minimumAgeRestriction = 0 # assume All Ages as default
        else:
            event_section.minimumAgeRestriction = age_restriction

        # ticket prices
        price_paragraph = intro_description_soup.find('p', text=re.compile("^(Free|\$).+"))
        if price_paragraph is not None:
            price_paragraph = price_paragraph.get_text()
            prices = showspiderutils.check_text_for_prices(showspiderutils.kill_unicode_and_strip(price_paragraph))
            if prices['doors'] is not None:
                event_section.ticketPriceDoors = prices['doors']
            if prices['advance'] is not None:
                event_section.ticketPriceAdvance = prices['advance']

        # sold out
        sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        if len(sold_out_selectors) > 0:
            event_section.soldOut = True

        # ticket purchase URL
        body_buttons = response.css('.eventitem-column-content .sqs-block-button a')
        for index, button in enumerate(body_buttons):
            button_text = button.css('a::text').extract_first()
            if re.match(r'buy|ticket', button_text, flags=re.IGNORECASE) is not None:
                ticket_purchase_url_string = button.css('a::attr(href)').extract_first()
                event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        # date
        date_string = response.css('.eventitem time.event-date::attr(datetime)').extract_first()  # YYYY-MM-DD
        # time
        time_string = response.css('.eventitem time.event-time-12hr-start::text').extract_first()  # H:MM PM

        event_section.startDatetime = arrow.get(time_string + " " + date_string, [r"h:mm a YYYY-MM-DD"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))


        # PERFORMERS SECTION
        # find performers
        performers = response.css('.eventitem-column-content .sqs-block-content h2')
        performances = []
        for i, performer in enumerate(performers):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer.css('::text').extract_first())
            performance_section.order = i
            performer_url = performer.css('a::attr(href)').extract_first()
            if performer_url is not None and len(performer_url) > 0:
                performance_section.urls = [performer_url]
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
