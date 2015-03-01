# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class ShowItem(scrapy.Item):
    title = scrapy.Field() 
    start = scrapy.Field() #arrow date obj
    room = scrapy.Field()
    url = scrapy.Field()
    venueUrl = scrapy.Field()
    performers = scrapy.Field() # array of performer strings

