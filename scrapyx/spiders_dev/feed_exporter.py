# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

""" 
HOW TO USE

scrapy crawl feed_exporter -a tbl=test_tbl

# Feed types: csv/xml/json/jsonlines
# STORAGE_BACKEND: local/s3/ftp

"""
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request

import re, json, string, csv, sys, os
from datetime import datetime
from dateutil import tz
import time

from MySQLdb import escape_string
try:
    from urllib.parse import unquote
except ImportError:
    from urlparse import unquote

from scrapyx.items import BaseItemLoader
from scrapyx.utils.utils import * 
from bson.objectid import ObjectId
from bson import json_util

_config = read_json('config/common.json')
env = _config['environment']
common_config = _config[env]

_creds_config = read_json('config/creds.json')
creds_config = _creds_config[env]

DB_TYPE = common_config['db_type']
FEED_FORMAT = common_config['feed_format']
STORAGE_BACKEND  = common_config['storage']

if DB_TYPE == 'mysql':
    from scrapyx.utils.mysql import *  
if DB_TYPE == 'postgres':
    from scrapyx.utils.postgres import * 
if DB_TYPE == 'mongo':
    from scrapyx.utils.mongo import * 

# We have custom item loader for each site to offload data processing logic from spider
class FeedExporterItemLoader(BaseItemLoader):
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

class FeedExporterSpider(scrapy.Spider):
    name = 'feed_exporter'
    allowed_domains = ['google.com']
    start_urls = [
        'https://www.google.com/'
    ]

    base_url = 'https://www.google.com'  

    db = None     
    tbl_export = ''

    FEED_EXPORT_FIELDS = (
        '_id',
        'text',
        'image',
        'file_rename',
        'downloaded'
    )                                     

    # Custom settings
    FEED_EXPORT_INDENT = 0
    if FEED_FORMAT in ['json', 'xml', 'jsonlines']:
        FEED_EXPORT_INDENT = 4

    FEED_EXT = FEED_FORMAT
    if FEED_FORMAT == 'jsonlines':
        FEED_EXT = 'jsonl'
    
    custom_settings = {
        #'DOWNLOAD_DELAY': 1,
        #'USER_AGENT': 'Mozilla/5.0 Firefox/62.0',
        'FEED_FORMAT': FEED_FORMAT,
        'FEED_URI': 'output/{}/%(name)s_%(time)s.{}'.format(FEED_FORMAT, FEED_EXT),
        'FEED_EXPORT_INDENT': FEED_EXPORT_INDENT,
        'FEED_EXPORT_FIELDS': FEED_EXPORT_FIELDS,
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

    if STORAGE_BACKEND == 's3':
        FEED_URI = 's3://{}/%(name)s_%(time)s.{}'.format(creds_config['BUCKET_NAME'], FEED_FORMAT)
        custom_settings.update({            
            'FEED_URI': FEED_URI,
            'AWS_ACCESS_KEY_ID': creds_config['AWS_ACCESS_KEY_ID'],
            'AWS_SECRET_ACCESS_KEY': creds_config['AWS_SECRET_ACCESS_KEY'],    
            'AWS_DEFAULT_REGION': creds_config['AWS_DEFAULT_REGION']
            })

    if STORAGE_BACKEND == 'ftp':
        FEED_URI = 'ftp://{user}:{passwd}@{host}/{path}/%(name)s_%(time)s.{FEED_FORMAT}'.\
        format(user=creds_config['FTP_USER'], 
            passwd=creds_config['FTP_PASS'],
            host=creds_config['FTP_HOST'],
            path=creds_config['FTP_PATH'],
            FEED_FORMAT=FEED_FORMAT)

        custom_settings.update({            
            'FEED_URI': FEED_URI,
            'FEED_STORAGE_FTP_ACTIVE': creds_config['FEED_STORAGE_FTP_ACTIVE']
            })

    handle_httpstatus_list = [307, 400, 404, 405, 416, 456]

    dont_redirect = False

    test_urls = ['https://www.google.com/']

    def __init__(self, *args, **kwargs):
        super(FeedExporterSpider, self).__init__(*args, **kwargs)

        self.machine = common_config['machine']
        self.limit = common_config['limit']       

        # Init DB connection
        if DB_TYPE:
            self.db = Database()   

        if 'tbl' in kwargs.keys():
            self.tbl_export = kwargs['tbl']            

    def parse(self, response):     
        if not DB_TYPE or not self.tbl_export:
            return
        if DB_TYPE in ['postgres', 'mysql']:    
            if self.limit:        
                select_query = "SELECT * FROM {} WHERE {} LIMIT {}".format(self.tbl_export, '1', self.limit)
            else:
                select_query = "SELECT * FROM {} WHERE {}".format(self.tbl_export, '1')
            rows = self.db.select(select_query)
            
        elif DB_TYPE in ['mongo']:
            _filter = {}
            results = self.db.select(_filter, self.tbl_export, self.limit) 
            rows = []           
            for r in results:
                row = {}
                for key in r.keys():
                    value = r[key]
                    if type(value) is ObjectId:
                        value = str(value)  
                    if type(value) is list or type(value) is dict:
                        value = json.dumps(value, default=json_util.default)

                    row[key] = value
                rows.append(row)

        for row in rows:
            yield row

    def closed(self, reason="Closed"):
        mesg = "{} - Spider {} closed!".format('FEED', self.name)
        sendAlert(mesg)
