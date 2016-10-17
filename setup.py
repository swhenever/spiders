# Automatically created by: scrapyd-deploy

from setuptools import setup, find_packages

setup(
    name         = 'showoff_scrape',
    version      = '0.1',
    packages     = find_packages(),
    entry_points = {'scrapy': ['settings = showoff_scrape.settings']},
)
