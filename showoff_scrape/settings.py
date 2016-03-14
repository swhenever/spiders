# -*- coding: utf-8 -*-

import os
from os.path import join, dirname
from dotenv import load_dotenv

# Scrapy settings for showoff_scrape project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

# Load environment variables
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_NAME = 'showoff_scrape'

SPIDER_MODULES = ['showoff_scrape.spiders']
NEWSPIDER_MODULE = 'showoff_scrape.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'showoff_scrape (+http://www.yourdomain.com)'

ITEM_PIPELINES = {
    'showoff_scrape.pipelines.ShowoffScrapePipeline': 500,
}

# Location of the engine endpoint for creating showbills
ENGINE_SHOWBILL_ENDPOINT = os.environ.get("ENGINE_SHOWBILL_ENDPOINT")