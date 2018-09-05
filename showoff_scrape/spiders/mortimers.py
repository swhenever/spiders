from scrapy.spiders import BaseSpider
import arrow
import showspiderutils
import dateutil
import re
import urllib2
import json
try:
    # Python 2.6-2.7 
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3
    from html.parser import HTMLParser
from showoff_scrape.items import *


class MortimersSpider(scrapy.spiders.Spider):

    name = 'mortimers'
    allowed_domains = ['mortimersbar.com', 'sociablekit.com', 'facebook.com']
    start_urls = ['https://www.sociablekit.com/app/embed/facebook-events/widget_events_json.php?embed_id=6174&show=upcoming']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier("Mortimer's", 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'https://www.mortimersbar.com'
        return venue_section

    def parse(self, response):
        h = HTMLParser()
        jsonresponse = json.loads(response.body_as_unicode())
        self.logger.info("response events length is %s", len(jsonresponse["events"]))
        for showdata in jsonresponse["events"]:
          if showdata["start_time"]:
            self.logger.info("parse_show")
            # DISCOVERY SECTION
            discovery_section = showspiderutils.make_discovery_section('mortimers.py')
            discovery_section.foundUrl = showdata["event_fb_link"]

            # VENUE SECTION
            venue_section = self.make_venue_section()

            # EVENT SECTION
            event_section = EventSection()
            event_section.eventUrl = showdata["event_fb_link"]


            # date/time
            # 2018-06-15 22:00:00
            event_section.startDatetime = arrow.get(showdata["start_time_raw"], [r"YYYY-MM-DD HH:mm"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            if showdata["end_time_raw"]:
              event_section.endDatetime = arrow.get(showdata["end_time_raw"], [r"YYYY-MM-DD HH:mm"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

            # ticket purchase URL
            if showdata["ticket_uri"]:
              event_section.ticketPurchaseUrl = showdata["ticket_uri"]

            # title
            title = showspiderutils.kill_unicode_and_strip(h.unescape(showdata["name"]))
            title = re.sub(r' at Mort.*', '', title, flags=re.IGNORECASE)
            event_section.title = title

            # price
            # this data is locked up in facebook event description text

            # age restriction
            # TODO the occasional early (brunch) show is all ages?
            event_section.minimumAgeRestriction = 21

            # performances
            # extended info about performers is usually in FB event description text, but alas unavailable
            performances = []
            performers = showspiderutils.parse_text_for_performers(title)
            for i, performer in enumerate(performers):
              performance_section = PerformanceSection()
              performance_section.name = performer
              performance_section.order = i
              performances.append(performance_section)

            # MAKE HipLiveMusicShowBill
            showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

            # Make Scrapy ShowBill container item
            scrapy_showbill_item = ScrapyShowBillItem(showbill)
            self.logger.info("about to yield title %s", title)
            yield scrapy_showbill_item
