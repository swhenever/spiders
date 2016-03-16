import scrapy
from scrapy.selector import Selector
import arrow
import dateutil
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class ThreeThirtyOneClubSpider(scrapy.Spider):

    name = 'threethirtyoneclub'
    allowed_domains = ['331.mn']
    start_urls = ['http://www.331.mn/events.php']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('331 Club', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://www.331.mn/'
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = '331club.py'
        return discovery_section


    def parse(self, response):
        #inspect_response(response, self)

        # current year
        year = arrow.now().format('YYYY')

        # regex for "#:##pm"
        timeRegex = re.compile("[0-9:]+pm")

        # the events calendar table 
        # 1st TABLE > 2nd TR > TD > TABLE > 4th TR
        eventContentRow = response.selector.xpath("(((//body//table)[1]/tr)[2]/td/table/tr)[4]")

        # Day TR > TD > DIV > TABLE > TR > 
        #   the second TD contains date info
        #   the fourth TD contains event info (in DIV.event_copy_full)
        dayRows = eventContentRow.xpath("td/div/table/tr/td")
        for index, dayRow in enumerate(dayRows):
            # get arrays of strings from appropriate table cells within the event row
            dayInfo = dayRow.xpath("(div/table/tr/td)[2]//text()").extract()
            eventLines = dayRow.xpath("(div/table/tr/td)[4]//text()").extract()

            # get date stuff for this dayRow
            day = dayInfo[2] # 3rd row in event area
            month = dayInfo[1] # 2nd row in event area

            # Parse events in this dayRow
            # one event typically ends with "XXXXpm"
            # typically starts with a SPAN at the start of the DIV.event_copy_full OR two BRs
            currentEventLines = []
            for eventIndex, eventLine in enumerate(eventLines):
                # if we have a "[0-9]pm" then we're at a line that ends an event
                if timeRegex.match(eventLine):
                    # see if we have collected event lines
                    if (len(currentEventLines) > 0):
                        # cool, create a date now that we have time
                        time = timeRegex.findall(eventLine)[0]
                        # make sure we have a full time string
                        if time.find(":") == -1:
                            time = time.replace("pm", ":00pm")

                        # DISCOVERY SECTION
                        discovery_section = self.make_discovery_section()
                        discovery_section.foundUrl = response.url

                        # VENUE SECTION
                        venue_section = self.make_venue_section()
                
                        # EVENT SECTION
                        event_section = EventSection()
                        event_section.startDatetime = arrow.get(month + " " + day + " " + year + " " + time, 'MMMM D YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))

                        # assume these are performers
                        performances = []
                        for i, performer in enumerate(currentEventLines):
                            performance_section = PerformanceSection()
                            performance_section.name = performer
                            performance_section.order = i
                            performances.append(performance_section)

                        # MAKE HipLiveMusicShowBill
                        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

                        # Make Scrapy ShowBill container item
                        scrapy_showbill_item = ScrapyShowBillItem(showbill)

                        #done
                        yield scrapy_showbill_item

                    # whether we've collected lines or not, time to reset
                    currentEventLines = []
                elif len(eventLine.strip()) > 0:
                    # collect this line, it is nonzero and not a time
                    currentEventLines.append(eventLine)
