import scrapy
from scrapy.selector import Selector
import arrow
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response


class LeesLiquorLoungeSpider(scrapy.Spider):

    name = 'leesliquorlounge'
    allowed_domains = ['leesliquorlounge.com']
    start_urls = ['http://www.leesliquorlounge.com/calcomplete.html']
    # rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Lee\'s Liquor Lounge', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.leesliquorlounge.com/'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'leesliquorlounge.py'
        return discovery_section

    def parse(self, response):
        # inspect_response(response, self)

        # regex for "#:##pm" or ""
        timeRegex = re.compile("[0-9][0-9:]+[ ?][am|pm]+")

        # regex for "####" - match a year string
        yearRegex = re.compile("\d\d\d\d")

        # regex for one or more #s - match a day string
        dayRegex = re.compile("[0-9]+")

        # event and date info are in DIVs inside the DIV.main
        # events are identified as DIV.event1 and month info is (mostly) identified as DIV.calHeader
        divs = response.selector.css('div.main > div')

        for index, div in enumerate(divs):
            # make sure this is either an event DIV or a calendar month DIV
            # if this is a calendar month header, set the current month/year to it
            if len(div.css(".calHeader")) == 1 and len(yearRegex.findall(div.extract())) > 0:
                # get month and year
                currentMonthYear = arrow.get(div.xpath("text()").extract()[0], "MMMM YYYY")

            if len(div.css(".event1")) == 1:
                # get the date
                dateString = dayRegex.findall(div.css("div.eventDate::text").extract()[0])[0]

                # get an array of the band names
                performers = div.css("div.eventDesc a.band::text").extract()

                # get an array of the possible time strings
                # this is text NOT in A tags
                timePossibilities = div.css("div.eventDesc::text").extract()
                goodTimePos = []
                for timeIndex, timePossibility in enumerate(timePossibilities):
                    if len(timeRegex.findall(timePossibility)) > 0:
                        # verified to have a time, we think
                        goodTimePos.append(timePossibility)

                # if we have at least one time possibility remaining, then create events
                # @todo raise an error if number of time possibilities doesn't match number of performers
                if len(goodTimePos) > 0:
                    for pIndex, performer in enumerate(performers):
                        # DISCOVERY SECTION
                        discovery_section = self.make_discovery_section()
                        discovery_section.foundUrl = response.url

                        # VENUE SECTION
                        venue_section = self.make_venue_section()

                        # EVENT SECTION
                        event_section = EventSection()
                        event_section.eventUrl = response.url
                        # log.msg("pIndex: " + str(pIndex) + ", goodTimePos: " + str(goodTimePos) + ", performers: " + str(performers), level=log.DEBUG)
                        timeString = timeRegex.findall(goodTimePos[pIndex])[0]
                        monthString = currentMonthYear.format('MMMM')
                        yearString = currentMonthYear.format('YYYY')
                        # log.msg("attempted time string:" + monthString + " " + dateString + " " + yearString + " " + timeString.replace(' ', ''), level=log.DEBUG)
                        event_section.startDatetime = arrow.get(monthString + " " + dateString + " " + yearString + " " + timeString.replace(' ', ''), 'MMMM D YYYY h:mma')

                        # PERFORMERS SECTION
                        # assume these are performers
                        performance_section = PerformanceSection()
                        performance_section.name = performer
                        performance_section.order = 0
                        performances_section = [performance_section]

                        # MAKE HipLiveMusicShowBill
                        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances_section)

                        # Make Scrapy ShowBill container item
                        scrapy_showbill_item = ScrapyShowBillItem(showbill)

                        #done
                        yield scrapy_showbill_item
