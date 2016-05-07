# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import arrow
import scrapy


class VenueIdentifier(object):
    def __init__(self, name, city, state):
        self.name = name
        self.city = city
        self.state = state


class ShowBillSection(object):
    def __init__(self):
        self.sourceDocument = str
        self.otherData = dict

    # Omit properties that not set (built in str, float, dict, int) when generating object state
    # this is used by jsonpickle, so our json representation doesn't have useless properties
    def __getstate__(self):
        clone = {}
        for key, value in self.__dict__.iteritems():
            if isinstance(value, arrow.arrow.Arrow):
                clone[key] = value.to('utc').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z'
            # @todo the below is dumb
            elif value != str and value != dict and value != float and value != int and value != list and value != arrow.arrow.Arrow:
                clone[key] = value

        return clone


class DiscoverySection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.foundUrl = str
        self.foundDateTime = arrow.utcnow()
        self.discoveredBy = str


class VenueSection(ShowBillSection):
    def __init__(self, venueIdentifier=VenueIdentifier):
        ShowBillSection.__init__(self)
        self.venueIdentifier = venueIdentifier
        self.stage = str
        self.venueUrl = str


class EventSection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.doorsDatetime = arrow.arrow.Arrow
        self.startDatetime = arrow.arrow.Arrow
        self.endDatetime = arrow.arrow.Arrow
        self.minimumAgeRestriction = int
        self.ticketPriceDoors = float
        self.ticketPriceAdvance = float
        self.ticketUrl = str
        self.soldOut = False
        self.eventUrl = str
        self.title = str
        self.description = str


class PerformanceSection(ShowBillSection):
    def __init__(self):
        ShowBillSection.__init__(self)
        self.name = str
        self.description = str
        self.order = int
        self.startDateTime = arrow.arrow.Arrow
        self.urls = list


class ShowBill(object):
    def __init__(self, discovery=DiscoverySection, venue=VenueSection, event=EventSection):
        self.discoverySection = discovery
        self.venueSection = venue
        self.eventSection = event


class HipLiveMusicShowBill(ShowBill):
    def __init__(self, discovery=DiscoverySection, venue=VenueSection, event=EventSection, performances=list):
        ShowBill.__init__(self, discovery, venue, event)
        self.performancesSection = performances


class ScrapyShowBillItem(scrapy.Item):
    showbill = scrapy.Field()

    def __init__(self, showbill):
        scrapy.Item.__init__(self)
        self['showbill'] = showbill

'''
Build a HipLiveMusicShowBill

# DISCOVERY
discoverySection = DiscoverySection()
discoverySection.foundUrl = 'http://first-avenue.com/event/2015/08/tallestmanonearth'
discoverySection.discoveredBy = 'firstave.py'
discoverySection.sourceDocument = '<html><body>the whole HTML document I found</body></html>'

# VENUE
venue = VenueIdentifier('First Avenue', 'Minneapolis', 'Minnesota')
venue_section = VenueSection(venue)
venue_section.venueUrl = 'http://www.first-avenue.com'

# EVENT
event_section = EventSection()
event_section.doorsDatetime = arrow.get('2015-08-29 20:00:00', 'YYYY-MM-DD HH:mm:ss')
event_section.minimumAgeRestriction = '18+'
event_section.ticketPriceAdvance = 30.00
event_section.ticketPriceDoors = 30.00
event_section.eventUrl = 'http://first-avenue.com/event/2015/08/tallestmanonearth'
event_section.otherData = {
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
showbill = HipLiveMusicShowBill(discoverySection, venue_section, event_section, performances_section)
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

