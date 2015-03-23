# -*- coding: utf-8 -*-
import requests
from scrapy.exceptions import DropItem
from scrapy import log
from pprint import pprint

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ShowoffScrapePipeline(object):
	venueId = False

	def open_spider(self, spider):
		#log.msg("yo opened spider", level=log.DEBUG)
		# get the venue ID for our spider from the API
		# right now clumsy: getting all venues
		endpoint = 'http://127.0.0.1:8000/venues/'
		venuesResponse = requests.get(endpoint)
		for venue in venuesResponse.json():
			if venue['url'] == spider.venueIdentifyingUrl:
				#log.msg("found matching venue", level=log.DEBUG)
				self.venueId = venue['id']
				break

		if self.venueId == False:
			# didn't find the venue, so let's create one
			venuePayload = { 'name' : spider.venueLabel, 'url' : spider.venueIdentifyingUrl }
			venuePostResponse = requests.post(endpoint, data=venuePayload)
			#log.msg("about to post payload", level=log.DEBUG)
			if venuePostResponse.status_code != requests.codes.created:
				# could not save a venue, something is wrong and events are not going to work
				#log.msg("something wrong with saving venue, status code: " + str(venuePostResponse.status_code) + " text: " + venuePostResponse.text, level=log.DEBUG)
				venuePostResponse.raise_for_status()
			else:
				self.venueId = venuePostResponse.json()['id']
				#log.msg("venue post response json id: " + str(venuePostResponse.json()['id']), level=log.DEBUG)

	def process_item(self, item, spider):
		#log.msg("Self venue id: " + str(self.venueId), level=log.DEBUG)

		# Make API call to save item
		eventEndpoint = 'http://127.0.0.1:8000/events/'
		eventPayload = {
			'title' : item['title'],
			'venue' : self.venueId,
			'start' : item['start'].format('YYYY-MM-DD') + "T" + item['start'].format('HH:mm:ss') + "Z",
			'room'	: item.get('room', ''),
			'url'	: item['url']
		}
		log.msg("EventPayload Vars: venue: " + str(self.venueId) + ", room: " + item.get('room', 'cat'), level=log.DEBUG)
		eventResponse = requests.post(eventEndpoint, data=eventPayload)

		# does this event already exist?
		if eventResponse.status_code == 409:
			raise DropItem("Existing ShowItem found: %s" % item['url'])

		elif eventResponse.status_code == requests.codes.created:
			# Make API call to save each of the performers and add each to the event
			performerEndpoint = 'http://127.0.0.1:8000/performers/'
			performerEventListingEndpoint = 'http://127.0.0.1:8000/performer-event-listings/'
			for i, performer in enumerate(item['performers']):
				# Save the performer. API will return the existing Performer if duplicate is found.
				performerPayload = {
					'name' : performer
				}
				performerRequest = requests.post(performerEndpoint, data=performerPayload)

				# Save the Performer Event Listing (ties the performer to the event)
				performerEventListingPayload = {
					'performer' : performerRequest.json()['id'],
					'event' : eventResponse.json()['id'],
					'order' : i
				}
				performerEventListingResponse = requests.post(performerEventListingEndpoint, data=performerEventListingPayload)

			return item

		else: 
			# we got an unexpected status code
			eventResponse.raise_for_status()
