import scrapy
from scrapy.selector import Selector
import arrow
import re
from showoff_scrape.items import *
from scrapy.shell import inspect_response

class ThreeThirtyOneClubSpider(scrapy.Spider):

    name = 'threethirtyoneclub'
    venueIdentifyingUrl = 'http://www.331.mn'
    venueLabel = '331 Club'
    allowed_domains = ['331.mn']
    start_urls = ['http://www.331.mn/events.php']
    #rules = [Rule(LinkExtractor(allow=['/event/\d+/\d+/.+']), 'parse_show')]

    def parse(self, response):
        #inspect_response(response, self)

    	# start with an empty show
    	show = ShowItem()

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

                        # assume these are performers
                        show['performers'] = currentEventLines
                        show['title'] = ', '.join(currentEventLines)
                        show['start'] = arrow.get(month + " " + day + " " + year + " " + time, 'MMMM D YYYY h:mma')
                        # construct a fake anchor + url to use as a unique identifier
                        url = self.venueIdentifyingUrl + "/#" + year + "-" + month + "-" + day + "-" + time
                        show['url'] = url

                        #done
                        yield show

                    # whether we've collected lines or not, time to reset the show info
                    show = ShowItem()
                    currentEventLines = []
                elif len(eventLine.strip()) > 0:
                    # collect this line, it is nonzero and not a time
                    currentEventLines.append(eventLine)
