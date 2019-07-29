from scrapy.spiders import Spider
import arrow
import re
import showspiderutils
import jsonpickle
from showoff_scrape.items import *


class MoonpalaceSpider(Spider):
    name = 'moonpalace'
    allowed_domains = ['musicatmoonpalace.com']
    start_urls = ['https://www.musicatmoonpalace.com/shows']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Moon Palace', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'https://www.musicatmoonpalace.com'
        return venue_section

    def parse(self, response):
        # Get site content hidden in a javascript variable
        scripts = response.css('script::text').extract()
        content_script = list(filter(lambda script: re.match(r"^\s*var warmupData", script) is not None, scripts))[0]
        json_match = re.match("^\s*var warmupData\s+=\s*({.+});", content_script)
        content_json = json_match.group(1)
        content_data = jsonpickle.decode(content_json)

        # Get events data out of content data
        generated_key = content_data['tpaWidgetNativeInitData'].keys()[0]  # 'comp-jg3gu6hl'
        events = content_data['tpaWidgetNativeInitData'][generated_key]['wixCodeProps']['state']['events']

        for event in events:
            # Useful data from the event object
            title = event['title']
            description = event['description']
            slug = event['slug']
            start_date_string = event['scheduling']['config']['startDate']
            # end_date_string = event['scheduling']['config']['endDate']

            # DISCOVERY SECTION
            discovery_section = showspiderutils.make_discovery_section('moonpalace.py')
            discovery_section.foundUrl = response.url

            # VENUE SECTION
            venue_section = self.make_venue_section()

            # EVENT SECTION
            event_section = EventSection()
            event_section.eventUrl = venue_section.venueUrl + '/events/' + slug

            # title
            event_section.title = title

            # price
            possible_prices = showspiderutils.check_text_for_prices(description)
            if possible_prices['doors'] is not None:
                event_section.ticketPriceDoors = possible_prices['doors']
            if possible_prices['advance'] is not None:
                event_section.ticketPriceAdvance = possible_prices['advance']

            # age restriction
            possible_age_restriction = showspiderutils.check_text_for_age_restriction(description)
            if possible_age_restriction is not None:
                event_section.minimumAgeRestriction = possible_age_restriction

            # ticket purchase
            # TODO: ok, if we scrape the url, the ticket link is in there *somewhere* - but I don't know where

            # time/date
            event_section.startDatetime = arrow.get(start_date_string).to(self.timezone)

            # performances
            performances = []
            performer_strings = showspiderutils.parse_text_for_performers(title)
            for i, performer in enumerate(performer_strings):
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


# OTHER WAYS TO GET DATA FROM MAIN PAGE HTML
# container           event  date/time
# response.css('#wix-events-widget ._1EOAT ._2Cofy::attr(aria-label)').extract()
#       => Jul 28, 12:30 PM \u2013 2:30 PM

#               container           event  event title
# response.css('#wix-events-widget ._1EOAT [data-hook="ev-list-item-title"]::text').extract()
#       => Making Spaces Safer: A Workshop With Shawna Potter
#       => Hive record release with Wanderer, Blue Ox, and Conscripts
#       => Rachel Lime | FPA | The Melancholy Boy
