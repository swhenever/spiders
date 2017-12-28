from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
import datetime
import showspiderutils
import dateutil
from showoff_scrape.items import *

class TicketFlySpider(CrawlSpider):

    allowed_domains = ['ticketfly.com']

    rules = [
        Rule(LinkExtractor(allow=['/event/.+']), 'parse_show'),
    ]

    def make_ticketfly_event_section(self, response):
        event_section = EventSection()
        event_section.eventUrl = response.url

        # TITLE
        event_section.title = response.css('.event-content .event-titles h1.headliners::text').extract_first()

        # DATE
        day = response.css('.event-content .event-date .event-date-day::text').extract_first() #D
        month = response.css('.event-content .event-date .event-date-month::text').extract_first() #MMM
        current_year = arrow.now().format('YYYY')
        current_month = arrow.now().format('M')
        if int(current_month) > int(arrow.get(month, 'MMM').format('M')):
            year = str(int(current_year) + 1)
        else:
            year = current_year

        # TIME
        start_times = doors_times = []
        start_time_text = response.css('.event-venue .event-start-time span.start::text').extract_first() #h:mm A
        if start_time_text is not None:
            start_times = showspiderutils.check_text_for_times(start_time_text)
        doors_time_text = response.css('.event-venue .event-start-time span.doors::text').extract_first()
        if doors_time_text is not None:
            doors_times = showspiderutils.check_text_for_times(doors_time_text)
        if len(start_times) > 0:
            event_section.startDatetime = arrow.get(month + " " + day + " " + year + " " + start_times[0], 'MMM D YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))
        if len(doors_times) > 0:
            event_section.doorsDatetime = arrow.get(month + " " + day + " " + year + " " + doors_times[0], 'MMM D YYYY h:mma').replace(tzinfo=dateutil.tz.gettz(self.timezone))

        # AGE RESTRICTION
        restriction_text = response.css('.event-venue .age-restriction::text').extract_first()
        if restriction_text is not None:
            restriction = showspiderutils.check_text_for_age_restriction(restriction_text)
            if restriction is not None:
                event_section.minimumAgeRestriction = restriction
        
        # PRICE
        prices = showspiderutils.check_text_for_prices(response.css('.event-tickets .event-tickets-price::text').extract_first())
        if prices['doors'] is not None:
            event_section.ticketPriceDoors = prices['doors']
        if prices['advance'] is not None:
            event_section.ticketPriceAdvance = prices['advance']
        
        # TICKET URL
        ticket_url = response.css('.event-tickets .ticket-link2 a::attr(href)').extract_first()
        if ticket_url is not None:
            event_section.ticketPurchaseUrl = ticket_url
        
        return event_section

    def make_ticketfly_performance_section(self, response):
        performances = []
        performance_chunks = response.css('.event-details .artist-box-support, .event-details .artist-box-headliner')

        for index, performance in enumerate(performance_chunks):
            performance_section = PerformanceSection()
            performance_section.name = performance.css('.artist-name::text').extract_first()
            performance_section.order = index

            links = performance.css('ul.external-links li a::attr(href)').extract()
            if links is not None:
                performance_section.urls = links

            performances.append(performance_section)
        
        return performances