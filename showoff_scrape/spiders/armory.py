import arrow
import showspiderutils
from showoff_scrape.items import *
import dateutil
import re
import json
from bs4 import BeautifulSoup
import scrapy


class ArmorySpider(scrapy.spiders.Spider):

    name = 'armory'
    allowed_domains = ['armorymn.com']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier("Armory", 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'https://armorymn.com'
        return venue_section

    def start_requests(self):
        params = {
            'action': 'more_post_ajax',
            'offset': '0',
            'ppp': '50'
        }
        yield scrapy.FormRequest('https://armorymn.com/wp-admin/admin-ajax.php', callback=self.parse,
                                 method='POST', formdata=params)

    def parse(self, response):
        events = response.css('article')
        for event in events:
            self.logger.info("parse_show")

            # EVENT SECTION
            event_section = EventSection()

            # DISCOVERY SECTION
            discovery_section = showspiderutils.make_discovery_section('armory.py')
            links = event.css('.post_links a')
            for link in links:
                if link.css('a::text').extract_first() == 'more info':
                    discovery_section.foundUrl = link.css('a::attr(href)').extract_first()
                    event_section.eventUrl = link.css('a::attr(href)').extract_first()

            # VENUE SECTION
            venue_section = self.make_venue_section()

            # EVENT SECTION con't

            # date/time
            now = arrow.now()
            date_content = event.css('.post_date p').extract_first()
            date_content = date_content.strip('<p>').strip('</p>')
            date_parts = list(map(lambda x: x.strip(), re.split('<br.+?>', date_content)))
            time_parts = showspiderutils.check_text_for_times(date_parts[2])
            # see if this event is this year or next
            test_date = arrow.get(now.format("YYYY") + " " + date_parts[1] + " " + time_parts[0], [r"YYYY MMMM Do H:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            if test_date < now:
                year_part = now.shift(years=-1).format("YYYY")
            else:
                year_part = now.format("YYYY")
            if len(time_parts) > 1:
                event_section.doorsDatetime = arrow.get(year_part + " " + date_parts[1] + " " + time_parts[0], [r"YYYY MMMM Do H:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
                event_section.startDatetime = arrow.get(year_part + " " + date_parts[1] + " " + time_parts[1], [r"YYYY MMMM Do H:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            else:
                event_section.startDatetime = arrow.get(year_part + " " + date_parts[1] + " " + time_parts[0], [r"YYYY MMMM Do H:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))

            # ticket purchase URL
            event_section.ticketPurchaseUrl = event.css('.btn-tickets::attr(href)').extract_first()

            # title
            title = showspiderutils.kill_unicode_and_strip(event.css('h2.post-title a::text').extract_first())
            event_section.title = title

            # price
            # price data probably on ticket purchase page...

            # age restriction
            meta_soup = BeautifulSoup(event.css('.post_date').extract_first(), "lxml")
            meta_text = meta_soup.get_text().strip()
            age = showspiderutils.check_text_for_age_restriction(meta_text)
            if age is not None:
                event_section.minimumAgeRestriction = age

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
