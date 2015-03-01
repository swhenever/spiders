# -*- coding: utf-8 -*-
import requests

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ShowoffScrapePipeline(object):
	venueId = False

	# def open_spider(spider):
	# 	# get the venue ID for our spider from the API
	# 	# right now clumsy: getting all venues
	# 	endpoint = 'http://127.0.0.1:8000/venues/'
	# 	venuesResponse = requests.get(endpoint)
	# 	for venue in venuesResponse:
	# 		if venue.url == spider.venueIdentifyingUrl:
	# 			self.venueId = venue.id
	# 			break

	def process_item(self, item, spider):
		# get the venue ID for our spider from the API
		# right now clumsy: getting all venues
		if self.venueId == False:
			endpoint = 'http://127.0.0.1:8000/venues/'
			venuesResponse = requests.get(endpoint)
			for venue in venuesResponse.json():
				if venue['url'] == spider.venueIdentifyingUrl:
					self.venueId = venue['id']
					break

		# Make API call to save item
		eventEndpoint = 'http://127.0.0.1:8000/events/'
		eventPayload = {
			'title' : item['title'],
			'venue' : self.venueId,
			'start' : item['start'].format('YYYY-MM-DD') + "T" + item['start'].format('HH:mm:ss') + "Z",
			'room'	: item['room'],
			'url'	: item['url']
		}
		eventResponse = requests.post(eventEndpoint, data=eventPayload)

		# Make API call to save each of the performers and add each to the event
		#performerEndpoint = 'http://127.0.0.1:8000/performers/'
		#for performer in item.performers


		return item
