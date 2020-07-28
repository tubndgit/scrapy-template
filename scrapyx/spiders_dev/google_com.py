# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

""" 
HOW TO RUN

scrapy crawl google_com -a test=4

# test = 1: Testing insert/update/delete DB
# test = 2: Testing insert many
# test = 3: Testing select mongodb
# test = 4: Testing update item
# test = 5: Testing download images from mongodb
# test = 6: Testing download images from mysql/postgres

"""
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request

import re, json, string, csv, sys, os
from datetime import datetime
from dateutil import tz
import time

from fuzzywuzzy import fuzz
from MySQLdb import escape_string
try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote

from scrapyx.items import BaseItemLoader
from scrapyx.utils.utils import * 
from bson.objectid import ObjectId

_config = read_json('config/common.json')
common_config = _config[_config['environment']]

DB_TYPE = common_config['db_type']
FEED_FORMAT = common_config['feed_format']
if DB_TYPE == 'mysql':
    from scrapyx.utils.mysql import *  
if DB_TYPE == 'postgres':
    from scrapyx.utils.postgres import * 
if DB_TYPE == 'mongo':
    from scrapyx.utils.mongo import * 

# We have custom item loader for each site to offload data processing logic from spider
class GoogleComItemLoader(BaseItemLoader):
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

class GoogleComSpider(scrapy.Spider):
    name = 'google_com'
    allowed_domains = ['google.com']
    start_urls = [
        'https://www.google.com/'
    ]

    base_url = 'https://www.google.com'  

    db = None     

    deny_url = ()

    lx_sections = LinkExtractor(restrict_css=('a.types__list'),
                                allow=(r'/category/'), deny=deny_url)

    lx_sub_sections = LinkExtractor(restrict_css=('div.types__list>a'),
                                allow=(r'/product/'), deny=deny_url)

    lx_items = LinkExtractor(restrict_css=('div.types__list>a'), allow=())

    item_headers = generate_headers(base_url, '1')
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
            'scrapyx.pipelines.ScrapyxDatabaseExporterPipeline': 300
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

    test_urls = ['https://www.google.com/']

    def __init__(self, *args, **kwargs):
        super(GoogleComSpider, self).__init__(*args, **kwargs)

        self.machine = common_config['machine']
        self.limit = common_config['limit']       

        # Init DB connection
        self.db = Database()        

        self.test_case = int(kwargs['test'])        

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
        l = GoogleComItemLoader(response=response)  
        item = l.load_item()
        #Testing insert/update/delete DB
        if self.test_case == 1:
            item = {
                'text': u'Bärte liegen aktuell\' absolut im Trend und sind mehr als nur eine modisches Accessoire. Sie symbolisieren Männlichkeit, unterstreichen den Charakter und stehen für eine ganze Lebenseinstellung. Doch wenn es darum geht, sich für einen Bart zu entscheiden, stehen Sie vor einer Fülle an Möglichkeiten. Allerdings ist nicht jeder Bart für jedes Gesicht und jeden Haarwuchs geeignet. Außerdem sind einige Bärte wesentlich pflegeintensiver als andere. Sehen Sie nun eine Auswahl der aktuell beliebtesten Bärte.'
            }

            items = [
                {
                    'text': u'Bärte liegen aktuell\' absolut im Trend und sind mehr als nur eine '
                },
                {
                    'text': u'Bärte liegen aktuell\' absolut im Trend und si'
                }
                ]

            update_item = {
                'text': u'Bärte liegen aktuell\' absolut'
            }

            # Testing insert
            _id = self.db.insert(item, 'test_tbl')   
            print("Inserted one: {}".format(_id))
            _ids = self.db.insert_multiple(items, 'test_tbl')
            print("Inserted many: {}".format(_ids))

            # Testing update
            #where = {'_id': ObjectId(_id)} # For mongo
            where = '"id"={}'.format(_id)
            modified_count = self.db.update_row(update_item, where, 'test_tbl')
            print("Updated count: {}".format(modified_count))

            # Testing delete
            #deleted_count = self.db.delete(where, 'test_tbl')    
            #print("Deleted count: {}".format(deleted_count))

        # Testing insert many
        if self.test_case == 2:
            items = [
                {                
                    'text': u'Bärte liegen aktuell\' absolut im Trend und sind mehr als nur eine modisches Accessoire. Sie symbolisieren Männlichkeit, unterstreichen den Charakter und stehen für eine ganze Lebenseinstellung. Doch wenn es darum geht, sich für einen Bart zu entscheiden, stehen Sie vor einer Fülle an Möglichkeiten. Allerdings ist nicht jeder Bart für jedes Gesicht und jeden Haarwuchs geeignet. Außerdem sind einige Bärte wesentlich pflegeintensiver als andere. Sehen Sie nun eine Auswahl der aktuell beliebtesten Bärte.',
                    'image': u'https://img.chefkoch-cdn.de/rezepte/3809931580038457/bilder/1272012/crop-960x640/erdbeertorte-im-winter.jpg',
                    'file_rename': u'3809931580038457-bilder-1272012-crop-960x640-erdbeertorte-im-winter.jpg',
                    'downloaded': 0
                },
                {                
                    'text': u'Bärte liegen aktuell\' absolut im Trend und si',
                    'image': u'https://img.chefkoch-cdn.de/rezepte/3810651580060336/bilder/1272179/crop-960x640/exotische-linsenfrikadellen.jpg',                
                    'file_rename': u'3810651580060336-bilder-1272179-crop-960x640-exotische-linsenfrikadellen.jpg',
                    'downloaded': 0
                }
                ]

            item = {
                'db_table': 'test_tbl', 
                'is_many': True,
                'items': items
            }

            yield item

        # Testing select from mongo
        if self.test_case == 3:        
            query = { "text": { "$regex": "^Bärte liegen aktuell'" } }
            rows = self.db.select(query, 'test_tbl', 3) 
            for x in rows:   
                print(x)

        # Testing update item
        if self.test_case == 4:
            _item = {
                'text': u'Bärte liegen aktuell\' absolut'
            }
            item = {
                'db_table': 'test_tbl',
                'is_update': True,
                #'filter': {'_id': ObjectId('5e70874d02d71830ec29eec6')},
                'pk_id': 'id',
                'pk_value': 2,
                'item': _item
            }
            yield item

        # Test download images from mongo
        if self.test_case == 5:
            query = {}
            rows = self.db.select(query, 'test_tbl', 3) 

            for x in rows:
                file_item = {
                    'db_table': 'test_tbl', # required
                    'pk_id': '_id', # required
                    'pk_value': str(x['_id']), # required
                    'base_url': self.base_url, # required
                    'image_urls': [x['image']],
                    'rename': x['file_rename']           
                }

                yield file_item

        # Test download images from mysql/postgres
        if self.test_case == 6:
            query = "SELECT * FROM test_tbl WHERE downloaded=0"
            rows = self.db.select(query) 
            print(rows)

            for x in rows:
                file_item = {
                    'db_table': 'test_tbl', # required
                    'pk_id': 'id', # required
                    'pk_value': x['id'], # required
                    'base_url': self.base_url, # required
                    'image_urls': [x['image']],
                    'rename': x['file_rename']           
                }

                yield file_item


    def closed(self, reason="Closed"):
        mesg = "{} - Spider {} closed!".format('google.com', self.name)
        sendAlert(mesg)
