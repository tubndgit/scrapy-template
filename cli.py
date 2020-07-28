# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

"""
HOW TO USE

# 1.1 - Generate spider from /resource/template_spider.tpl

python cli.py --spider spider-name https://www.domain.com

# Example: 
python cli.py --spider https://www.google.com --> spider: google_com.py
python cli.py --spider scrape-events https://www.google.com --> scrape_events.py

------------------------------------------------------------
# 1.2 - Generate download files spider from /resource/template_download.tpl

python cli.py --download spider-name https://www.domain.com

# Example: 
python cli.py --download https://www.google.com --> spider: google_com.py
python cli.py --download scrape-events https://www.google.com --> scrape_events.py

------------------------------------------------------------
# 2 - Generate scrapy.item from template
# It will read fields from `resource/items_input.txt` 
# and gerenate Scrapy fields into `resource/items.py`

python cli.py --item i

------------------------------------------------------------
# 3 - Generate scrapy.item from table columns
# It will get column names from table 
# and gerenate Scrapy fields into `resource/items.py`

python cli.py --table table_name

------------------------------------------------------------

"""
import os
from scrapy.crawler import CrawlerProcess
import sys
import boto3
from scrapy.utils.project import get_project_settings
import argparse
import tldextract
import string, json
from scrapyx.utils.utils import * 

_config = read_json('config/common.json')
common_config = _config[_config['environment']]

DB_TYPE = common_config['db_type']
if DB_TYPE == 'mysql':
    from scrapyx.utils.mysql import *  
if DB_TYPE == 'postgres':
    from scrapyx.utils.postgres import * 
if DB_TYPE == 'mongo':
    from scrapyx.utils.mongo import * 

def cli(args):
    # Create spider from /resource/spider.tpl
    if args.spider:        
        params = args.spider        
        if len(params) > 1:
            url = params[1]
        else:
            url = params[0]

        url_parsed = tldextract.extract(url)  
        url_split = url.split('/')    

        DOMAIN_NAME = '{}.{}'.format(url_parsed.domain, url_parsed.suffix)
        BASE_URL = '/'.join(url_split[:3])

        if len(params) < 2:            
            SPIDER_NAME = DOMAIN_NAME.replace('-', '_').replace('.', '_')
            CLASS_NAME = ''.join([string.capwords(x) for x in SPIDER_NAME.split('_') if x])
        else:
            SPIDER_NAME = params[0].replace('-', '_')
            CLASS_NAME = ''.join([string.capwords(x) for x in SPIDER_NAME.split('_') if x])
        
        print("\nGenerating Spider from Template... \n\nscrapyx/spiders/{}.py".format(SPIDER_NAME))

        spider_tpl = read_file('templates/template_spider.tpl')
                
        _spider_tpl = spider_tpl.replace('{CLASS_NAME}', CLASS_NAME)\
            .replace('{SPIDER_NAME}', SPIDER_NAME)\
            .replace('{DOMAIN_NAME}', DOMAIN_NAME)\
            .replace('{ORIGINAL_URL}', url)\
            .replace('{BASE_URL}', BASE_URL)
        
        out_file = "scrapyx/spiders/{}.py".format(SPIDER_NAME)
        write_file(_spider_tpl, out_file, "w+")
        
        print("\nDONE !!!")

    if args.download:        
        params = args.download        
        if len(params) > 1:
            url = params[1]
        else:
            url = params[0]

        url_parsed = tldextract.extract(url)  
        url_split = url.split('/')    

        DOMAIN_NAME = '{}.{}'.format(url_parsed.domain, url_parsed.suffix)
        BASE_URL = '/'.join(url_split[:3])

        if len(params) < 2:            
            SPIDER_NAME = DOMAIN_NAME.replace('-', '_').replace('.', '_')
            CLASS_NAME = ''.join([string.capwords(x) for x in SPIDER_NAME.split('_') if x])
        else:
            SPIDER_NAME = params[0].replace('-', '_')
            CLASS_NAME = ''.join([string.capwords(x) for x in SPIDER_NAME.split('_') if x])
        
        print("\nGenerating Spider from Template... \n\nscrapyx/spiders/{}.py".format(SPIDER_NAME))

        spider_tpl = read_file('templates/template_download.tpl')
                
        _spider_tpl = spider_tpl.replace('{CLASS_NAME}', CLASS_NAME)\
            .replace('{SPIDER_NAME}', SPIDER_NAME)\
            .replace('{DOMAIN_NAME}', DOMAIN_NAME)\
            .replace('{ORIGINAL_URL}', url)\
            .replace('{BASE_URL}', BASE_URL)
        
        out_file = "scrapyx/spiders/{}.py".format(SPIDER_NAME)
        write_file(_spider_tpl, out_file, "w+")
        
        print("\nDONE !!!")

    # Generate scrapy.item from template
    if args.item:     
        print("\nGenerating ITEMS from Template...")   
                
        items_tpl = read_file('templates/items.tpl')
        items_input = read_lines('resource/items_input.txt')

        ITEMS = []
        FEED_EXPORT_FIELDS = []
        for i in items_input:
            scrapy_item = '{} = scrapy.Field()'.format(i)
            ITEMS.append(scrapy_item)
            export_field = "'{}'".format(i)
            FEED_EXPORT_FIELDS.append(export_field)

        _items_tpl = items_tpl.replace('{ITEMS}', '\n'.join(ITEMS))\
            .replace('{FEED_EXPORT_FIELDS}', ',\n'.join(FEED_EXPORT_FIELDS))

        write_file(_items_tpl, "resource/items.py", "w+")
        
        print("\nDONE !!!")

    # Generate scrapy.item from template
    if args.table:
        print("\nGenerating ITEMS from Table Columns...")
        
        items_tpl = read_file('templates/items.tpl')

        db = Database()
        table_name = args.table
        items_input = db.get_columns(table_name)

        ITEMS = []
        FEED_EXPORT_FIELDS = []
        for i in items_input:
            scrapy_item = '{} = scrapy.Field()'.format(i)
            ITEMS.append(scrapy_item)
            export_field = "'{}'".format(i)
            FEED_EXPORT_FIELDS.append(export_field)

        _items_tpl = items_tpl.replace('{ITEMS}', '\n'.join(ITEMS))\
            .replace('{FEED_EXPORT_FIELDS}', ',\n'.join(FEED_EXPORT_FIELDS))

        write_file(_items_tpl, "resource/items.py", "w+")

        print("\nDONE !!!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command lines')

    parser.add_argument('--spider', metavar='path', required=False, nargs='+', 
                        help='Generate spider from Website URL')

    parser.add_argument('--download', metavar='path', required=False, nargs='+', 
                        help='Generate download spider from Website URL')

    parser.add_argument('--item', metavar='path', required=False, 
                        help='Generate scrapy.item from resource/items_input.txt')

    parser.add_argument('--table', metavar='path', required=False, 
                        help='Generate scrapy.item from table name')

    args = parser.parse_args()    
    cli(args)