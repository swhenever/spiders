import scrapy
from scrapy.selector import Selector
import arrow
import dateutil
from bs4 import BeautifulSoup
import showspiderutils
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class ThreeThirtyOneClubSpider(scrapy.Spider):

    name = 'threethirtyoneclub'
    allowed_domains = ['331club.com']
    start_urls = ['http://331club.com/']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('331 Club', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://331club.com/'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = '331club.py'
        return discovery_section

    def parse_html_for_link(self, html):
        sel = Selector(text=html)
        text = sel.css('a::text').extract_first()
        href = sel.css('a::attr(href)').extract_first()

        if text is None:
            return None
        else:
            return [text, href]

    def parse(self, response):
        #inspect_response(response, self)
        # current year and month
        current_year = arrow.now().format('YYYY')
        current_month = arrow.now().format('M')

        # ticket price is always free ("never a cover")
        price = 0

        # age restriction always 21 (it's a bar)
        age_restriction = 21

        # Loop through events. Each "event" container may actually have two events
        for index, event in enumerate(response.css('div.event')):
            # get the date parts
            month = event.css('.event-date .month::text').extract_first()
            day = event.css('.event-date .date::text').extract_first()

            # if month is earlier than current month, then assume it is NEXT year
            if int(current_month) > int(arrow.get(month, 'MMM').format('M')):
                event_year = str(int(current_year) + 1)
            else:
                event_year = current_year

            # loop through columns: each column is an event
            for colindex, eventcol in enumerate(event.css('.event-content .columns .column')):
                soup = BeautifulSoup(eventcol.css('p').extract_first(), "lxml")
                lines = soup.p.get_text().strip().split('\n')

                # find time from last line, then drop last line from lines list
                times = showspiderutils.check_text_for_times(lines[-1])
                if len(times) is 0:
                    continue # we couldn't parse a time, so just skip this event altogether
                del lines[-1]

                # build performances from remaining lines
                performances = []
                for performer_index, performer_text in enumerate(lines):
                    performance_section = PerformanceSection()
                    performance_section.name = performer_text
                    performance_section.order = performer_index
                    performances.append(performance_section)

                # BUILD SHOWBILL

                # DISCOVERY SECTION
                discovery_section = self.make_discovery_section()
                discovery_section.foundUrl = response.url

                # VENUE SECTION
                venue_section = self.make_venue_section()
        
                # EVENT SECTION
                event_section = EventSection()
                event_section.startDatetime = arrow.get(month + " " + day + " " + event_year + " " + times[0], 'MMM D YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))
                event_section.ticketPriceDoors = price
                event_section.minimumAgeRestriction = age_restriction

                # MAKE HipLiveMusicShowBill
                showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

                # Make Scrapy ShowBill container item
                scrapy_showbill_item = ScrapyShowBillItem(showbill)

                #done
                yield scrapy_showbill_item
