import scrapy
from scrapy.selector import Selector
from scrapy import log
import arrow
import dateutil
from showoff_scrape.items import *

class KittyCatKlubSpider(scrapy.Spider):

    name = 'kittycatklub'
    allowed_domains = ['kittycatklub.net']
    start_urls = ['http://www.kittycatklub.net']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Kitty Cat Klub', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.kittycatklub.net'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'kittycatklub.py'
        return discovery_section

    def parse(self, response):
        # Get the month / year that is being displayed
        monthYearText = response.selector.css("span.headline::text").extract()[0]
        # log.msg("monthYearText: " + monthYearText.strip(), level=log.DEBUG)
        parts = monthYearText.strip().split(' ')
        month = parts[0].strip(' \t\n\r') # 'March'
        year = parts[1].strip(' \t\n\r') # '2015'
        defaultTime = '9:00pm' # Kitty Cat Klub doesn't really list times, so we're going to provide one

        # start with an empty show
        # show = ShowItem()
        event_section = EventSection()
        performances = []

        # kitty cat klub data is in the eighth nested table (!)
        #tds = response.selector.xpath("//table//table//table//table//table//table//table//table//tr/td/text()").extract();
        rowSelectors = response.selector.xpath("//table//table//table//table//table//table//table//table//tr")
        for index, row in enumerate(rowSelectors):
            # check what "kind" of row this is
            if len(row.xpath("td").css("span.date::text").extract()) > 0:
                # do date processing
                dayString = row.xpath("td").css("span.date::text").extract()[0]
                dayparts = dayString.split(' ')
                day = dayparts[0].strip(' \t\n\r')
                # log.msg("attempted time string:" + month + " " + day + " " + year + " " + defaultTime, level=log.DEBUG)
                date = arrow.get(month + " " + day + " " + year + " " + defaultTime, 'MMMM D YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))
                #show['start'] = date
                event_section.startDatetime = date

                # do price processing
                costString = row.xpath("td").css("span.cost::text").extract()[0]
                event_section.ticketPriceDoors = costString

            elif len(row.xpath("td[contains(@colspan, '5')]/text()").extract()) > 0:
                # do performer list processing
                performerStrings = row.xpath("td/text()").extract()
                for i, performerString in enumerate(performerStrings):
                    performerString = performerString.strip(' \t\n\r')
                    if len(performerString) > 0:
                        performance_section = PerformanceSection()
                        performance_section.name = performerString
                        performance_section.order = i
                        performances.append(performance_section)
                # show['performers'] = performers
                # show['title'] = ', '.join(performers)

            if hasattr(event_section, 'startDatetime') and len(performances) > 0:
                # our show is (almost) fully populated, so yield
                # DISCOVERY SECTION
                discovery_section = self.make_discovery_section()
                discovery_section.foundUrl = response.url

                # VENUE SECTION
                venue_section = self.make_venue_section()

                # MAKE HipLiveMusicShowBill
                showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

                # Make Scrapy ShowBill container item
                scrapy_showbill_item = ScrapyShowBillItem(showbill)

                yield scrapy_showbill_item

                # initialize a new show
                event_section = EventSection()
                performances = []
                #show = ShowItem()