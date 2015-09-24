# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import arrow
import scrapy


class VenueIdentifier(object):
    def __init__(self, venue_name, venue_city, venue_state):
        self.venue_name = venue_name
        self.venue_city = venue_city
        self.venue_state = venue_state


class ShowBillSection(object):
    def __init__(self):
        self.source_document = str
        self.other_data = dict

    # Omit properties that not set (built in str, float, dict) when generating object state
    # this is used by jsonpickle, so our json representation doesn't have useless properties
    def __getstate__(self):
        clone = {}
        for key, value in self.__dict__.iteritems():
            if isinstance(value, arrow.arrow.Arrow):
                clone[key] = value.to('utc').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z'
            # @todo the below is dumb
            elif value != str and value != dict and value != float and value != list and value != arrow.arrow.Arrow:
                clone[key] = value

        return clone


class DiscoverySection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.found_url = str
        self.found_datetime = arrow.utcnow()
        self.discovered_by = str


class VenueSection(ShowBillSection):
    def __init__(self, venue_identifier=VenueIdentifier):
        ShowBillSection.__init__(self)
        self.venue_identifier = venue_identifier
        self.room = str
        self.venue_url = str


class EventSection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.doors_datetime = arrow.arrow.Arrow
        self.start_datetime = arrow.arrow.Arrow
        self.end_datetime = arrow.arrow.Arrow
        self.age_restriction = str
        self.ticket_price_doors = float
        self.ticket_price_advance = float
        self.ticket_purchase_url = str
        self.sold_out = False
        self.event_url = str
        self.title = str
        self.description = str
        self.stage = str


class PerformancesSection(ShowBillSection):
    def __init__(self, performance_sections=list):
        ShowBillSection.__init__(self)
        self.performance_sections = performance_sections  # this should be a list of PerformanceSections


class PerformanceSection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.name = str
        self.description = str
        self.order = int
        self.time = arrow.arrow.Arrow
        self.urls = list


class ShowBill(object):
    def __init__(self, discovery=DiscoverySection, venue=VenueSection, event=EventSection):
        self.discovery_section = discovery
        self.venue_section = venue
        self.event_section = event


class HipLiveMusicShowBill(ShowBill):
    def __init__(self, discovery=DiscoverySection, venue=VenueSection, event=EventSection, performances=PerformancesSection):
        ShowBill.__init__(self, discovery, venue, event)
        self.performances_section = performances


class ScrapyShowBillItem(scrapy.Item):
    showbill = scrapy.Field()

    def __init__(self, showbill):
        scrapy.Item.__init__(self)
        self['showbill'] = showbill

'''
Build a HipLiveMusicShowBill

# DISCOVERY
discovery_section = DiscoverySection()
discovery_section.found_url = 'http://first-avenue.com/event/2015/08/tallestmanonearth'
discovery_section.discovered_by = 'firstave.py'
discovery_section.source_document = '<html><body>the whole HTML document I found</body></html>'

# VENUE
venue = VenueIdentifier('First Avenue', 'Minneapolis', 'Minnesota')
venue_section = VenueSection(venue)
venue_section.venue_url = 'http://www.first-avenue.com'

# EVENT
event_section = EventSection()
event_section.doors_datetime = arrow.get('2015-08-29 20:00:00', 'YYYY-MM-DD HH:mm:ss')
event_section.age_restriction = '18+'
event_section.ticket_price_advance = 30.00
event_section.ticket_price_doors = 30.00
event_section.ticket_purchase_url = 'https://www.etix.com/ticket/p/2538486/the-tallest-man-on-earth-minneapolis-first-avenue?cobrand=first-avenue'
event_section.event_url = 'http://first-avenue.com/event/2015/08/tallestmanonearth'
event_section.other_data = {
    'presented_by': ['89.3 The Current', 'City Pages'],
    'poster_image': 'http://first-avenue.com/sites/default/files/images/events/Tallest-Man-on-Earth-on-sale.jpg'
}

# PERFORMANCES
tallest_man = PerformanceSection()
tallest_man.name = 'The Tallest Man On Earth'
tallest_man.description = 'Dark Bird Is Home ... on earlier albums and singles.'
tallest_man.order = 1
tallest_man.urls = [
    'http://www.thetallestmanonearth.com/',
    'http://facebook.com/thetallestmanonearthofficial',
    'http://twitter.com/tallestman',
    'http://deadoceans.com/artist.php?name=tallestmanonearth',
    'https://www.youtube.com/watch?list=PLCs4qpIOzO-j9BH5UFzFH6grNERbcyltF&v=JFfDsfhLG4k'
]
lady_lamb = PerformanceSection()
lady_lamb.name = 'Lady Lamb'
lady_lamb.description = 'To many, Lady Lamb is an enigma....the before and the after.'
lady_lamb.order = 2
lady_lamb.urls = [
    'http://www.ladylambjams.com/',
    'http://www.facebook.com/ladylambjams',
    'http://twitter.com/ladylambjams',
    'http://soundcloud.com/ladylambthebeekeeper'
]
performances_section = PerformancesSection([tallest_man, lady_lamb])

# finally, SHOWBILL
showbill = HipLiveMusicShowBill(discovery_section, venue_section, event_section, performances_section)
'''

'''
YE OLDE SHOWITEM (obsolete)
class ShowItem(scrapy.Item):
    title = scrapy.Field() 
    start = scrapy.Field()  # arrow date obj
    room = scrapy.Field()
    url = scrapy.Field()
    venueUrl = scrapy.Field()
    performers = scrapy.Field()  # array of performer strings
'''

