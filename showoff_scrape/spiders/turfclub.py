import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
from showoff_scrape.items import ShowItem
from scrapy.shell import inspect_response

class TurfClubSpider(CrawlSpider):

    name = 'turfclub'
    venueIdentifyingUrl = 'http://www.turfclub.net'
    venueLabel = 'Turf Club'
    allowed_domains = ['turfclub.net']
    start_urls = ['http://turfclub.net/shows/']
    rules = [Rule(LinkExtractor(allow=['/show/\d\d\d\d-\d\d-.+']), 'parse_show')] #/show/2015-04-traster-pureka/

    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse_show(self, response):
        #inspect_response(response, self)
        show = ShowItem()

        show['url'] = response.url

        name_result = response.css('h2.rhp-event-header a::text').extract()
        show['title'] = self.kill_unicode_and_strip(name_result[0])

        date_string = response.css('div.rhp-event-details p.rhp-event-date::text').extract()
        date_string = self.kill_unicode_and_strip(date_string[0])
        time_string = response.css('div.rhp-event-details p.rhp-event-time::text').extract()
        time_string = self.kill_unicode_and_strip(time_string[0])

        date = arrow.get(date_string + " " + time_string, 'dddd, MMMM D, YYYY h:mm a')
        show['start'] = date

        # find performers
        performerStrings = response.css('div.tribe-events-single-event-description h2::text, div.tribe-events-single-event-description h3::text').extract()
        performers = []
        for i, performer in enumerate(performerStrings):
            performers.append(self.kill_unicode_and_strip(performer))
        show['performers'] = performers

        return show
