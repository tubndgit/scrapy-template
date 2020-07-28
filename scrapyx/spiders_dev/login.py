# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

""" 
HOW TO RUN

scrapy crawl login -a user=username -a pass=password

"""

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request, FormRequest

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
from loginform import fill_login_form
import logging

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
class LoginItemLoader(BaseItemLoader):
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

class LoginSpider(scrapy.Spider):
    name = 'login'
    allowed_domains = ['github.com']
    start_urls = [
        'https://github.com/tubndgit/scrapyx-template'
    ]

    base_url = 'https://github.com'  

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

    login_page = 'https://github.com/login'

    def __init__(self, *args, **kwargs):
        super(LoginSpider, self).__init__(*args, **kwargs)
        
        self.machine = common_config['machine']
        self.limit = common_config['limit']            

        # Init DB connection
        if DB_TYPE:
            self.db = Database()

        if 'user' in kwargs.keys():
            self.login_user = kwargs['user']

        if 'pass' in kwargs.keys():
            self.login_pass = kwargs['pass']      

        print(self.login_user, self.login_pass)  

    def start_requests(self):
        logging.log(logging.WARNING, "---------------Init request---------------")
        """This function is called before crawling starts."""
        yield scrapy.Request(url=self.login_page, callback=self.login, dont_filter=True)

    def login(self, response):
        """Generate a login request."""
        logging.log(logging.WARNING, "---------------Logging in---------------")
        args, url, method = fill_login_form(response.url, response.body, self.login_user, self.login_pass)
        return FormRequest(url, method=method, formdata=args, callback=self.check_login_response)

    def check_login_response(self, response):
        """Check the response returned by a login request to see if we are
        successfully logged in.
        """

        if response.css('label[for="password"]'):   
            logging.log(logging.WARNING, "Bad times :(")
            # Something went wrong, we couldn't log in, so nothing happens.
            return
        else:            
            logging.log(logging.WARNING, "---------------Successfully logged in. Let's start crawling!---------------")
            # Now the crawling can begin..                                
            cookies = parse_cookie(response)
            print(cookies)

            #return [scrapy.Request(url=url, cookies=cookies, dont_filter=True) for url in self.start_urls]
            return [scrapy.Request(url=url, dont_filter=True) for url in self.start_urls]

    def parse(self, response):     
        title = response.css('span[itemprop="about"]::text').get('').encode('utf-8')
        print(title)

    def closed(self, reason="Closed"):
        mesg = "{} - Spider {} closed!".format('github.com', self.name)
        sendAlert(mesg)
