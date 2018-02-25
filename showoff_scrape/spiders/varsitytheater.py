import scrapy
import arrow
import re
import jsonpickle
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response
import showspiderutils

class VarsitySpider(scrapy.spiders.Spider):

    name = 'varsitytheater'
    allowed_domains = ['varsitytheater.com']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Varsity Theater', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://varsitytheater.com'
        return venue_section

    def start_requests(self):
        # Make request to Varsity Theater API
        startDate = arrow.now().format('M/DD/YYYY')
        endDate = arrow.now().shift(years=+1).format('M/DD/YYYY')
        url = "http://www.varsitytheater.com/api/EventCalendar/GetEvents?startDate=" + startDate + "&endDate=" + endDate + "&venueIds=50144&limit=200&offset=1&offerType=STANDARD&genre=&artist="

        return [scrapy.Request(url, callback=self.parse_api)]

    def parse_api(self, response):
        # PARSE ENCODED JSON RESPONSE
        # response is a javascript string of JSON, which we decode a second time to get the actual data
        events = jsonpickle.decode(jsonpickle.decode(response.body))

        for i, event_data in enumerate(events["result"]):
            event_id = event_data["eventID"]
            offer_id = event_data["offerID"]
            url = "http://www.varsitytheater.com/EventDetail?tmeventid=" + str(event_id) + "&offerid=" + str(offer_id)
            yield scrapy.Request(url, callback=self.parse_show)

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('varsitytheater.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url

        # EXTRACT JS DATA
        # They use an SPA, which is loading from a javascript variable
        # couldn't find the actual API location for just a single event's details, so pulling from the page source
        event_records = re.findall("var RECORD =(.+?);\r\n", response.body.decode("utf-8"), re.S)
        event_data = jsonpickle.decode(jsonpickle.decode(event_records[0]))

        # TITLE
        event_section.title = event_data["content"]["title"]

        # TIME AND DATE
        event_section.startDatetime = arrow.get(event_data["content"]["eventDateStart"]).replace(tzinfo=dateutil.tz.gettz(self.timezone)) # 2018-03-02T20:00:00

        # AGE RESTRICTION
        age_restriction = showspiderutils.check_text_for_age_restriction(event_data["content"]["eventInfo"])
        if age_restriction is not None:
            event_section.minimumAgeRestriction = age_restriction

        # PRICE
        low_price = None
        sold_out = True
        for i, price_level in enumerate(event_data["content"]["priceLevels"]):
            if low_price is None or int(float(price_level["price"])) < low_price:
                low_price = int(float(price_level["price"]))
            if price_level["soldOut"] is False:
                sold_out = False
        if low_price is not None:
            event_section.ticketPriceAdvance = low_price

        # SOLD OUT
        event_section.soldOut = sold_out # see above

        # TICKET URL
        # following convention shown on their website
        event_section.ticketPurchaseUrl = "https://concerts.livenation.com/event/" + event_data["content"]["eventId"]

        # PERFORMANCES
        performances = []
        for i, performer_data in enumerate(event_data["content"]["artists"]):
            if performer_data["unMapped"] is False:
                performance_section = PerformanceSection()
                performance_section.name = performer_data["name"]
                performance_section.order = performer_data["rank"]
                performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
