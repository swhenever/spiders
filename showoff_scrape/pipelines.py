# -*- coding: utf-8 -*-
import requests
from scrapy.exceptions import DropItem
import logging
import jsonpickle
import json

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

class logPipeline(object):
    def process_item(selfself, item, spider):
        item_json = json.loads(jsonpickle.encode(item['showbill'], unpicklable=False))
        logging.info('Showbill recorded: ' + json.dumps(item_json, sort_keys=True, indent=4))

        return item


class submitShowbillPipeline(object):

    def process_item(self, item, spider):
        # this should be a ScrapyShowBillItem
        # @todo throw error/skip if not

        # ShowBill API will respond with one of three things
        # success: stored the showbill
        # duplicate: we already have this exact showbill, so did not store
        # error: something went wrong

        # Make a JSON document representing the ShowBill
        item_json = jsonpickle.encode(item['showbill'], unpicklable=False)
        submit_data = { 'showbill' : item_json }

        # Make API call to save item
        showbill_endpoint = spider.settings['ENGINE_SHOWBILL_ENDPOINT']
        showbill_response = requests.post(showbill_endpoint, data=submit_data)
        logging.info('Submmitted Showbill. Response code: ' + str(showbill_response.status_code))
        
        # does this event already exist?
        if showbill_response.status_code == 409:
            raise DropItem("Existing ShowBill found: %s" % item['showbill'].discoverySection.foundUrl)
        
        elif showbill_response.status_code == requests.codes.created:
            item['showbill'] = item_json
            return item
        
        else:
            # we got an unexpected status code
            showbill_response.raise_for_status()
