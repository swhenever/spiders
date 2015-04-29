import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import re
from showoff_scrape.items import ShowItem
from scrapy.shell import inspect_response

class TripleRockSpider(CrawlSpider):

    name = 'triplerock'
    venueIdentifyingUrl = 'http://www.triplerocksocialclub.com'
    venueLabel = 'Triple Rock Social Club'
    allowed_domains = ['triplerocksocialclub.com']
    start_urls = ['http://www.triplerocksocialclub.com/shows']
    rules = [Rule(LinkExtractor(allow=['/event/\d+-.+']), 'parse_show')] #/event/829471-denim-matriarch-minneapolis/

    # kill unicode regex
    def kill_unicode_and_strip(self, text):
        return re.sub(r'[^\x00-\x7f]',r'',text).strip()

    def parse_show(self, response):
        #inspect_response(response, self)
        show = ShowItem()

        show['url'] = response.url

        name_result = response.css('div.event-info h1.headliners::text').extract()
        show['title'] = self.kill_unicode_and_strip(name_result[0])

        datetime_string = response.css('div.event-info h2.times span.start span::attr(title)').extract()
        datetime_string = self.kill_unicode_and_strip(datetime_string[0])

        date = arrow.get(datetime_string, 'YYYY-MM-DDTHH:mm:ssZZ') # 2015-05-02T20:00:00-05:00
        show['start'] = date

        # find performers
        performerStrings = response.css('div.artist-boxes div.artist-headline span.artist-name::text').extract()
        performers = []
        for i, performer in enumerate(performerStrings):
            performers.append(self.kill_unicode_and_strip(performer))
        show['performers'] = performers

        return show
