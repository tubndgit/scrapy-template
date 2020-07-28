# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

""" 
HOW TO RUN

scrapy crawl {SPIDER_NAME}

"""

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request

import re, json, string, csv, sys, os
from datetime import datetime
from dateutil import tz
import time
from bson.objectid import ObjectId

from MySQLdb import escape_string
try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote

from scrapyx.items import BaseItemLoader
from scrapyx.utils.utils import * 

# Read common config
_config = read_json('config/common.json')
env = _config['environment']
common_config = _config[env]

DB_TYPE = common_config['db_type']
FEED_FORMAT = common_config['feed_format']

if DB_TYPE == 'mysql':
    from scrapyx.utils.mysql import *  
if DB_TYPE == 'postgres':
    from scrapyx.utils.postgres import * 
if DB_TYPE == 'mongo':
    from scrapyx.utils.mongo import * 

# We have custom item loader for each site to offload data processing logic from spider
class {CLASS_NAME}ItemLoader(BaseItemLoader):
    @staticmethod
    def image_urls_out(links, loader_context):        
        images = [loader_context['response'].urljoin(x) for x in links if x]
        return images[1:]

    @staticmethod
    def description_out(values, loader_context):        
        return '\n'.join([x.replace('\n', '').strip() for x in values if x.replace('\n', '').strip()])        

    @staticmethod
    def price_out(prices, loader_context):        
        return get_1st_number_from_st(''.join(prices))

    @staticmethod
    def sale_price_out(prices, loader_context):        
        return get_1st_number_from_st(''.join(prices))    

class {CLASS_NAME}Spider(scrapy.Spider):
    name = '{SPIDER_NAME}'
    allowed_domains = ['{DOMAIN_NAME}']
    start_urls = [
        '{ORIGINAL_URL}'
    ]

    base_url = '{BASE_URL}'  

    db = None    

    deny_url = ()

    lx_sections = LinkExtractor(restrict_css=('a.types__list'),
                                allow=(r'/category/'), deny=deny_url)

    lx_sub_sections = LinkExtractor(restrict_css=('div.types__list>a'),
                                allow=(r'/product/'), deny=deny_url)

    lx_items = LinkExtractor(restrict_css=('div.types__list>a'), allow=())

    item_headers = generate_headers(base_url, '1') # Set '0' to return empty headers
    ajax_headers = generate_headers(base_url, 'ajax')

    # Custom settings
    custom_settings = {
        #'DOWNLOAD_DELAY': 1,
        #'USER_AGENT': 'Mozilla/5.0 Firefox/62.0',
        #'FEED_FORMAT': FEED_FORMAT,
        #'FEED_URI': 'output/FEED_FORMAT/%(name)s_%(time)s.FEED_FORMAT'.replace('FEED_FORMAT', FEED_FORMAT),
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,            
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'random_useragent.RandomUserAgentMiddleware': 400,
            #'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
            #'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
            #'scrapyx.utils.proxy.CustomProxyMiddleware': 100,
            'scrapyx.utils.proxy.ScrapyxProxyMiddleware': 100,            
        },
        'ITEM_PIPELINES': {
            'scrapyx.pipelines.ScrapyxUniqueFilterPipeline': 200,
            #'scrapyx.pipelines.ScrapyxDownloadImagePipeline': 300,
            #'scrapyx.pipelines.ScrapyxDownloadImageFromDatabasePipeline': 300,
            #'scrapyx.pipelines.ScrapyxDatabaseExporterPipeline': 300
        },                        
        #'RANDOM_UA_PER_PROXY ': True,
        #'AUTOTHROTTLE_ENABLED': False,
        'RETRY_TIMES': 20,
        'PROXY_ENABLED': is_proxy_enabled(),
        'PROXY_URL': get_proxy_url(),        
        #'RETRY_HTTP_CODES': [500, 502, 503, 504, 401, 403, 408, 410, 303, 304]
        #'REDIRECT_MAX_TIMES': 1,
        #'CLOSESPIDER_ITEMCOUNT': 20, # Limit items to scrape for testing
    }

    handle_httpstatus_list = [307, 400, 404, 405, 416, 456]

    dont_redirect = False

    test_urls = []

    def __init__(self, *args, **kwargs):
        super({CLASS_NAME}Spider, self).__init__(*args, **kwargs)
        
        self.machine = common_config['machine']
        self.limit = common_config['limit']            

        # Init DB connection
        if DB_TYPE:
            self.db = Database()

    def parse(self, response):     
        if len(self.test_urls):
            for test_url in self.test_urls:
                yield scrapy.Request(test_url, self.parse_item, \
                meta={'dont_redirect': self.dont_redirect}, headers=self.item_headers)
            return

        for l in self.lx_sections.extract_links(response):                  
            yield scrapy.Request(l.url, self.parse_section, \
                meta={'dont_redirect': self.dont_redirect}, headers=self.item_headers)                                                

    def parse_section(self, response):
        for l in self.lx_items.extract_links(response):                  
            yield scrapy.Request(l.url, self.parse_item, \
                meta={'dont_redirect': self.dont_redirect}, headers=self.item_headers)

    def parse_item(self, response): 
        l = {CLASS_NAME}ItemLoader(response=response)  
        item = l.load_item()
        pass      

    def closed(self, reason="Closed"):
        mesg = "{} - Spider {} closed!".format('{DOMAIN_NAME}', self.name)
        sendAlert(mesg)
