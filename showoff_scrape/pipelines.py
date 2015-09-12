# -*- coding: utf-8 -*-
import requests
from scrapy.exceptions import DropItem
from scrapy import log
import jsonpickle
from pprint import pprint


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ShowoffScrapePipeline(object):

    def process_item(self, item, spider):
        # this should be a ScrapyShowBillItem
        # @todo throw error/skip if not

        # ShowBill API will respond with one of three things
        # success: stored the showbill
        # duplicate: we already have this exact showbill, so did not store
        # error: something went wrong

        # Make a JSON document representing the ShowBill
        item_json = jsonpickle.encode(item['showbill'], unpicklable=False)

        # Make API call to save item
        event_endpoint = 'http://127.0.0.1:8000/events/'
        log.msg("item_json: " + item_json, level=log.DEBUG)
        # event_response = requests.post(event_endpoint, data=item_json)
        #
        # # does this event already exist?
        # if event_response.status_code == 409:
        #     raise DropItem("Existing ShowBill found: %s" % item.discovery_section.found_url)
        #
        # elif event_response.status_code == requests.codes.created:
        #     return item
        #
        # else:
        #     # we got an unexpected status code
        #     event_response.raise_for_status()
