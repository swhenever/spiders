import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import dateutil
import re
from re import sub
from showoff_scrape.items import *

class FirstAveSpider(CrawlSpider):

    name = 'firstave'
    allowed_domains = ['first-avenue.com']
    start_urls = ['http://first-avenue.com/calendar']

    # @todo handle daylight savings?
    timezone = 'US/Central'

    # Avoid following links for past events
    now = arrow.now(timezone)
    now_year = now.format('YYYY')
    year_regex = '(?:' + now_year[:2] + '[' + now_year[2] + '][' + now_year[3] + '-9]|' + now_year[:2] + '[' + str(int(now_year[2]) + 1) + '-9][0-9])'
    now_month = now.format('MM')
    if now_month[0] == '0':
        month_regex = '(?:0[' + now_month[1] + '-9]|1[0-2])'
    else:
        month_regex = '1[' + now_month[1] + '-2]'

    rules = [
        Rule(LinkExtractor(allow=['/event/' + year_regex + '/' + month_regex + '/.+']), 'parse_show'),
        Rule(LinkExtractor(allow=['/calendar/all/' + year_regex + '-' + month_regex]))
    ]
    # /event/2015/02/rhettmiller
    # /calendar/all/2016-06


    def get_venue_info(self, venue_name):
        if venue_name == 'First Avenue':
            city = 'Minneapolis'
            url = 'http://www.first-avenue.com/'
        elif venue_name == 'Turf Club':
            city = 'Saint Paul'
            url = 'http://www.turfclub.net/'
        elif venue_name == 'Fine Line':
            city = 'Minneapolis'
            url = 'http://finelinemusic.com/'
        elif venue_name == 'The Cedar':
            city = 'Minneapolis'
            url = 'http://www.thecedar.org/'
        elif venue_name == 'Amsterdam Bar and Hall':
            city = 'Saint Paul'
            url = 'http://www.amsterdambarandhall.com/'
        elif venue_name == 'The Cabooze':
            city = 'Minneapolis'
            url = 'http://www.cabooze.com/'
        elif venue_name == 'Skyway Theatre':
            city = 'Minneapolis'
            url = 'http://skywaytheatre.com/'
        elif venue_name == 'Varsity Theater':
            city = 'Minneapolis'
            url = 'http://varsitytheater.org/'
        elif venue_name == 'Icehouse':
            city = 'Minneapolis'
            url = 'http://www.icehousempls.com/'
        else:
            return False

        return {'city': city, 'url': url}

    # Make venue identifier for this venue-based spider
    def make_venue_identifier(self, venue_name):
        venue_info = self.get_venue_info(venue_name)

        if venue_info:
            return VenueIdentifier(venue_name, venue_info['city'], 'Minnesota')
        else:
            return False

    def make_venue_section(self, venue_name):
        identifier = self.make_venue_identifier(venue_name)
        venue_info = self.get_venue_info(venue_name)
        if identifier:
            venue_section = VenueSection(identifier)
            venue_section.venueUrl = venue_info['url']
        else:
            venue_section = False
        return venue_section

    def make_discovery_section(self):
        discovery_section = DiscoverySection()
        discovery_section.discoveredBy = 'firstave.py'
        return discovery_section

    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]', r'', text).strip()

    def parse_show(self, response):
        # DISCOVERY SECTION
        discovery_section = self.make_discovery_section()
        discovery_section.foundUrl = response.url

        # VENUE SECTION
        venue_string = response.css('div.field-name-field-event-venue div.field-item a::text').extract()
        venue_string = self.kill_unicode_and_strip(venue_string[0])
        if len(venue_string) > 0:
            venue_section = self.make_venue_section(venue_string)
        else:
            return []  # Cannot make a Show for this event, because we don't understand its venue

        # EVENT SECTION
        event_section = EventSection()
        event_section.eventUrl = response.url

        name_result = response.xpath("//h1[@id='page-title']/text()").extract()
        event_section.title = name_result[0]

        # Age restriction
        age_string = response.css('div.field-name-field-event-age div.field-item::text').extract()
        if len(age_string) > 0:
            age_string = self.kill_unicode_and_strip(age_string[0])
            if age_string == 'ALL AGES':
                event_section.minimumAgeRestriction = 0
            elif age_string == '18+':
                event_section.minimumAgeRestriction = 18
            else:
                event_section.minimumAgeRestriction = 21

        # Ticket Availability
        soldout_string = response.css('div.field-name-field-event-status div.field-item a.sold_out::text').extract()
        if len(soldout_string) > 0:
            soldout_string = self.kill_unicode_and_strip(soldout_string[0])
            event_section.soldOut = True
        else:
            purchase_string = response.css('div.field-name-field-event-status div.field-item a.on_sale').xpath('@href').extract()
            if len(purchase_string) > 0:
                purchase_string = self.kill_unicode_and_strip(purchase_string[0])
                event_section.ticketPurchaseUrl = purchase_string

        # Ticket Price
        doors_price_string = response.css('div.field-name-field-event-door-price span.price::text').extract()
        if len(doors_price_string) > 0:
            doors_price_string = self.kill_unicode_and_strip(doors_price_string[0])
            event_section.ticketPriceDoors = float(sub(r'[^\d.]', '', doors_price_string))
        advance_price_string = response.css('div.field-name-field-event-price span.price::text').extract()
        if len(advance_price_string) > 0:
            advance_price_string = self.kill_unicode_and_strip(advance_price_string[0])
            event_section.ticketPriceAdvance = float(sub(r'[^\d.]', '', advance_price_string))

        # Stage
        stage_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-room ")]/text()').extract()
        if len(stage_string) > 0:
            venue_section.stage = stage_string[0]
        #show['venue'] = 'First Avenue' 
        #venue: #field-name-field-event-venue//a/text() 
        #"room": #field-name-field-event-room/text()

        date_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " datepart ")]/text()').extract() #date-display-single
        date_string = date_string[0]
        time_string = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-date ")]//span[contains(concat(" ", normalize-space(@class), " "), " date-display-single ")]/text()').extract()
        time_string = time_string[0]
        time_string_parts = time_string.split('at');
        time_string = time_string_parts[1]

        date = arrow.get(date_string.strip() + " " + time_string.strip(), [r"\w+, MMMM D, YYYY h:mma"], locale='en').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        event_section.doorsDatetime = date

        # PERFORMANCES SECTION
        performer_strings = response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " field-name-field-event-performer ")]//article[contains(concat(" ", normalize-space(@class), " "), " node-performer ")]//h2//a/text()').extract() #field-name-field-event-performer
        performances = []
        for i, performer in enumerate(performer_strings):
            performance_section = PerformanceSection()
            performance_section.name = performer
            performance_section.order = i
            performances.append(performance_section)

        # MAKE HipLiveMusicShowBill
        showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances)

        # Make Scrapy ShowBill container item
        scrapy_showbill_item = ScrapyShowBillItem(showbill)

        return scrapy_showbill_item
