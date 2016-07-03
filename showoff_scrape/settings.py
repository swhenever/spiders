# -*- coding: utf-8 -*-

import os

# Scrapy settings for showoff_scrape project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'showoff_scrape'

SPIDER_MODULES = ['showoff_scrape.spiders']
NEWSPIDER_MODULE = 'showoff_scrape.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'showoff_scrape (+http://www.yourdomain.com)'

ITEM_PIPELINES = {
    'showoff_scrape.pipelines.logPipeline': 100,
}

# By default we submit showbills to Engine, but this can be disabled with an environment variable
SUBMIT_SHOWBILLS = os.environ.get("SUBMIT_SHOWBILLS")
if SUBMIT_SHOWBILLS == '1' or SUBMIT_SHOWBILLS is None:
    ITEM_PIPELINES['showoff_scrape.pipelines.submitShowbillPipeline'] = 500

# Location of the engine endpoint for creating showbills
ENGINE_SHOWBILL_ENDPOINT = os.environ.get("ENGINE_SHOWBILL_ENDPOINT")