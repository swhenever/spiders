import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
import arrow
import dateutil
import re
from re import sub
from showoff_scrape.items import *


def kill_unicode_and_strip(text, replacement=None):
    if replacement is None:
        replacement = ''
    return re.sub(r'[^\x00-\x7f]', r'' + replacement + '', text).strip()


# Normalize time string to 4:30pm format
def time_normalize(time_string):
    am_or_pm = re.search(ur'(am|pm)', time_string, re.IGNORECASE)
    if am_or_pm:
        am_or_pm = am_or_pm.group(0)
    else:
        am_or_pm = 'pm'  # assume pm
    time = re.sub('[^0-9:]', '', time_string)  # leave only numbers, colon
    if not re.search(r':', time):
        time += ':00'  # assume it is something like "4" or "12" and just add minutes
    return time + am_or_pm


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


def check_text_for_age_restriction(subject_text):
    if re.search(r'all ages|aa', subject_text, re.IGNORECASE):
        return 0
    elif re.search(r'\d\d\+', subject_text, re.IGNORECASE):
        return int(re.search(r'\d\d\+', subject_text, re.IGNORECASE).group().strip('+'))
    elif re.search(r'\d\d and over|\d\d & over', subject_text, re.IGNORECASE):
        return int(re.search(r'(\d\d)(?: and over)|(\d\d)(?: & over)', subject_text, re.IGNORECASE).groups()[0])
    else:
        return None


def check_text_for_prices(subject_text):
    prices = {'doors': None, 'advance': None}
    if re.search(ur'no cover|free', subject_text, re.IGNORECASE):
        prices['doors'] = 0
    else:
        prices_found = re.findall(ur'[$]\d+(?:\.\d{2})?', subject_text)
        if len(prices_found) > 1:
            # assume that door price is listed first
            prices['advance'] = float(prices_found[0].strip('$'))
            prices['doors'] = float(prices_found[1].strip('$'))

            # @todo support additional prices (VIP, table seating, etc.)
        elif len(prices_found) == 1:
            prices['doors'] = float(prices_found[0].strip('$'))
    return prices


# Possible time formats covered: 8, 8:30, 8pm, 8:30pm, 8 PM. Prefers times with am/pm string adjacent.
def check_text_for_times(subject_text):
    # Plan A: try times with am/pm text adjacent
    times = re.findall(ur'\d?\d\s*?[ap]m|\d?\d:\d{2}\s*?[ap]m', subject_text, re.IGNORECASE)
    if len(times) == 0:
        # Plan B: try finding times without am/pm
        times = re.findall(ur'\d?\d:\d{2}|\d?\d', subject_text, re.IGNORECASE)

    # Return in standardized format
    times = [time_normalize(time) for time in times]

    return times
