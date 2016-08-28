import scrapy
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors import LinkExtractor
import arrow
import dateutil
import re
from re import sub
from showoff_scrape.items import *


def kill_unicode_and_strip(text):
    return re.sub(r'[^\x00-\x7f]', r'', text).strip()


def make_discovery_section(script_name):
    discovery_section = DiscoverySection()
    discovery_section.discoveredBy = script_name
    return discovery_section


def check_text_for_cancelled(subject_text):
    return re.search(r'cancelled|canceled', subject_text, re.IGNORECASE)


def check_text_for_postponed(subject_text):
    return re.search(r'postponed', subject_text, re.IGNORECASE)


def check_text_for_moved(subject_text):
    return re.search(r'moved\s+to|was\s+moved|has\s+been\s+moved', subject_text, re.IGNORECASE)
