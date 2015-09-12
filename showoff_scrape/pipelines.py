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
        # log.msg("yo opened spider", level=log.DEBUG)
        # get the venue ID for our spider from the API
        # right now clumsy: getting all venues
        endpoint = 'http://127.0.0.1:8000/venues/'
        venues_response = requests.get(endpoint)
        for venue in venues_response.json():
            if venue['url'] == spider.venueIdentifyingUrl:
                # log.msg("found matching venue", level=log.DEBUG)
                self.venueId = venue['id']
                break

        if self.venueId == False:
            # didn't find the venue, so let's create one
            venue_payload = {'name': spider.venueLabel, 'url': spider.venueIdentifyingUrl}
            venue_post_response = requests.post(endpoint, data=venue_payload)
            # log.msg("about to post payload", level=log.DEBUG)
            if venue_post_response.status_code != requests.codes.created:
                # could not save a venue, something is wrong and events are not going to work
                # log.msg("something wrong with saving venue, status code: " + str(venue_post_response.status_code) + " text: " + venue_post_response.text, level=log.DEBUG)
                venue_post_response.raise_for_status()
            else:
                self.venueId = venue_post_response.json()['id']
            # log.msg("venue post response json id: " + str(venue_post_response.json()['id']), level=log.DEBUG)

    def process_item(self, item, spider):
        # log.msg("Self venue id: " + str(self.venueId), level=log.DEBUG)

        # Make API call to save item
        event_endpoint = 'http://127.0.0.1:8000/events/'
        event_payload = {
            'title': item['title'],
            'venue': self.venueId,
            'start': item['start'].format('YYYY-MM-DD') + "T" + item['start'].format('HH:mm:ss') + "Z",
            'room': item.get('room', ''),
            'url': item['url']
        }
        log.msg("EventPayload Vars: venue: " + str(self.venueId) + ", room: " + item.get('room', 'cat'),
                level=log.DEBUG)
        event_response = requests.post(event_endpoint, data=event_payload)

        # does this event already exist?
        if event_response.status_code == 409:
            raise DropItem("Existing ShowItem found: %s" % item['url'])

        elif event_response.status_code == requests.codes.created:
            # Make API call to save each of the performers and add each to the event
            performer_endpoint = 'http://127.0.0.1:8000/performers/'
            performer_event_listing_endpoint = 'http://127.0.0.1:8000/performer-event-listings/'
            for i, performer in enumerate(item['performers']):
                # Save the performer. API will return the existing Performer if duplicate is found.
                performer_payload = {
                    'name': performer
                }
                performer_request = requests.post(performer_endpoint, data=performer_payload)

                # Save the Performer Event Listing (ties the performer to the event)
                performer_event_listing_payload = {
                    'performer': performer_request.json()['id'],
                    'event': event_response.json()['id'],
                    'order': i
                }
                performer_event_listing_response = requests.post(performer_event_listing_endpoint,
                                                              data=performer_event_listing_payload)

            return item

        else:
            # we got an unexpected status code
            event_response.raise_for_status()
