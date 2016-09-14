import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import dateutil
from showoff_scrape.items import *
from scrapy.shell import inspect_response
import showspiderutils


class FineLineSpider(CrawlSpider):

    name = 'fineline'
    allowed_domains = ['finelinemusic.com']
    start_urls = ['http://finelinemusic.com/events/']
    rules = [Rule(LinkExtractor(allow=['/event/.+/']), 'parse_show')]  # /event/cold-kingdom-late-night-fights-special-guests-the-zealots-and-early-june/

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self):
        return VenueIdentifier('Fine Line', 'Minneapolis', 'Minnesota')

    def make_venue_section(self):
        venue_section = VenueSection(self.make_venue_identifier())
        venue_section.venueUrl = 'http://finelinemusic.com'
        return venue_section

    def parse_title_artists(self, title):
        artist_strings = []

        # get rid of "special guests"
        title = re.sub(r'special guests', r'', title, 0, re.IGNORECASE)

        # handle "Cal Ecker w/ Amanda Watkins"
        if re.search(r'w/', title, re.IGNORECASE):
            artist_strings += map(lambda p: showspiderutils.kill_unicode_and_strip(p), re.split(r'w/', title))
        elif re.search(r'\W&\W|\Wand\W', title, re.IGNORECASE):
            artist_strings += map(lambda p: showspiderutils.kill_unicode_and_strip(p), re.split(r'\W&\W|\Wand\W|,\W', title))
        else:
            artist_strings.append(title)

        return artist_strings

    def parse_show(self, response):
        #inspect_response(response, self)

        # DISCOVERY SECTION
        discovery_section = showspiderutils.make_discovery_section('fineline.py')
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_section = self.make_venue_section()

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url
        name_result = response.css('header.title div.title-container h1::text').extract()
        event_section.title = showspiderutils.kill_unicode_and_strip(name_result[0])

        post_paragraphs = response.css('div.single-post-content p::text').extract()

        # is event canceled?
        # there is a "status" element, the second of two div.cell in div.single-post-status
        # usually it is "Tickets Available" but also "CANCELED" or "MOVED TO 7TH ST ENTRY"
        status_cells = response.css('div.single-post-status div.cell::text').extract()
        if len(status_cells) == 2:
            status_text = showspiderutils.kill_unicode_and_strip(status_cells[1])
        else:
            status_text = ''
        if showspiderutils.check_text_for_cancelled(event_section.title) \
                or showspiderutils.check_text_for_cancelled(status_text):
            event_section.isCancelled = True
        if showspiderutils.check_text_for_moved(event_section.title) \
                or showspiderutils.check_text_for_moved(status_text):
            venue_section.wasMoved = True

        # age restriction
        # sometimes age restriction is in the last paragraph of the general "post" content
        if len(post_paragraphs) > 0:
            possible_age_restriction = post_paragraphs[(len(post_paragraphs) - 1)]
            ages = re.findall(ur'(\d+\+|all ages)', showspiderutils.kill_unicode_and_strip(possible_age_restriction))
            if len(ages) > 0 and ages[0] == 'all ages':
                event_section.minimumAgeRestriction = 0
            elif len(ages) > 0:
                event_section.minimumAgeRestriction = ages[0].strip(' +')

        # ticket prices
        # string is like: $15 Advance | $20 DOS
        # sometimes there is a third line for reserved balcony seating, but we're ignoring that
        ticket_price_string = response.css('div.single-post-price div.cell::text').extract()
        ticket_price_string = showspiderutils.kill_unicode_and_strip(ticket_price_string[1])
        prices = showspiderutils.check_text_for_prices(ticket_price_string)
        if prices['doors'] is not None:
            event_section.ticketPriceDoors = prices['doors']
        if prices['advance'] is not None:
            event_section.ticketPriceAdvance = prices['advance']

        # sold out
        # didn't find a sold out indicator on current calendar, so not sure yet what it will look like!
        # sold_out_selectors = response.css('div.ticket-price h3.sold-out::text').extract()
        # if len(sold_out_selectors) > 0:
        #     event_section.soldOut = True

        # ticket purchase URL
        ticket_purchase_url_string = response.css('div.post-buy.button a::attr(href)').extract()
        if len(ticket_purchase_url_string) > 0:
            ticket_purchase_url_string = showspiderutils.kill_unicode_and_strip(ticket_purchase_url_string[0])
            event_section.ticketPurchaseUrl = ticket_purchase_url_string

        # parse doors date/time
        # we assume "pm" for all fine line events
        date_string = response.css('li.single-post-date h3::text').extract()  # 07/27/2016
        date_string = showspiderutils.kill_unicode_and_strip(date_string[0])

        show_times_string = response.css('div.single-post-time div.cell::text').extract()  # 7:00 Doors | 7:30 Show
        show_times_string = showspiderutils.kill_unicode_and_strip("".join(show_times_string))
        show_times = re.findall(ur'\d+:\d+(?=\W)?(?=[ap]m)?', show_times_string)
        if len(show_times) > 1:
            event_section.doorsDatetime = arrow.get(date_string + show_times[0] + 'pm', [r"MM/DD/YYYYh:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
            event_section.startDatetime = arrow.get(date_string + show_times[1] + 'pm', [r"MM/DD/YYYYh:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        elif len(show_times) == 1:
            event_section.doorsDatetime = arrow.get(date_string + show_times[0] + 'pm', [r"MM/DD/YYYYh:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        else:
            # If we can't find any times, ShowBill would be incomplete.
            # @todo some way of logging this perhaps
            return []

        # PERFORMERS SECTION
        # find performers
        performer_strings = []

        # sometimes title includes multiple artists, sometimes it is just one.
        performer_strings += self.parse_title_artists(event_section.title)

        # sometimes there is a "W/ Artist Name" paragraph near the bottom of the post
        if len(post_paragraphs) > 0:
            for i, paragraph in enumerate(post_paragraphs):
                if i >= (len(post_paragraphs) - 4) and re.search(r'w/', paragraph, re.IGNORECASE):
                    possible_performer = showspiderutils.kill_unicode_and_strip(re.sub(r'w/', r'', paragraph, 0, re.IGNORECASE))
                    if possible_performer not in performer_strings:
                        performer_strings.append(possible_performer)

        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = showspiderutils.kill_unicode_and_strip(performer)
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
