# -*- coding: utf-8 -*-
import os.path
from scrapy.exceptions import DropItem
from scrapy.pipelines.files import FilesPipeline
import scrapy
import json
from bson.objectid import ObjectId
from scrapyx.utils.utils import * 

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

_config = read_json('config/common.json')
common_config = _config[_config['environment']]

DB_TYPE = common_config['db_type']
if DB_TYPE == 'mysql':
    from scrapyx.utils.mysql import *  
if DB_TYPE == 'postgres':
    from scrapyx.utils.postgres import * 
if DB_TYPE == 'mongo':
    from scrapyx.utils.mongo import * 

class ScrapyxDownloadImagePipeline(FilesPipeline):
    """
    Modified FilesPipeline that stores data in site subdirectories
    and returns pipeline-delimited list of file paths
    """
    DELIMITER = '|'
    
    def __init__(self, *args, **kwargs):
        super(ScrapyxDownloadImagePipeline, self).__init__(*args, **kwargs)

    def item_completed(self, results, item, info):
        if isinstance(item, dict) or self.files_result_field in item.fields:
            item[self.files_result_field] = self.DELIMITER.join([x['path'] for ok, x in results if ok])        
        
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            raise DropItem("Item contains no files")

        item['file_paths'] = file_paths        

        return item

    def get_media_requests(self, item, info):
        item_headers = generate_headers(item['base_url'], 'image')
        for file_url in item['image_urls']:
            if file_url:                
                yield scrapy.Request(
                    file_url
                    , meta={'item': item} 
                    , headers=item_headers
                )

    def file_path(self, request, response=None, info=None):
        item = request.meta['item']
        return os.path.join(info.spider.name, item['rename'])

    """
    def file_path(self, request, response=None, info=None):
        file_path = super(DownloadImagePipeline, self).file_path(request, response, info)
        return os.path.join(info.spider.name, file_path[file_path.index('/') + 1:].split('?')[0])
    """

class ScrapyxDownloadImageFromDatabasePipeline(FilesPipeline):
    """
    Modified FilesPipeline that stores data in site subdirectories
    and returns pipeline-delimited list of file paths
    """
    DELIMITER = '|'

    db = None
    
    def __init__(self, *args, **kwargs):
        super(ScrapyxDownloadImageFromDatabasePipeline, self).__init__(*args, **kwargs)
        
        self.db = Database()

    def item_completed(self, results, item, info):
        db_table = item['db_table']
        pk_id = item['pk_id']
        pk_value = item['pk_value']
        
        if DB_TYPE == 'mongo':
            where_clause = {str(pk_id): ObjectId(pk_value)}
        elif DB_TYPE == 'mysql':            
            where_clause = u'{}={}'.format(pk_id, pk_value)
        elif DB_TYPE == 'postgres':
            where_clause = u'"{}"={}'.format(pk_id, pk_value)

        if isinstance(item, dict) or self.files_result_field in item.fields:
            item[self.files_result_field] = self.DELIMITER.join([x['path'] for ok, x in results if ok])        
        
        file_paths = [x['path'] for ok, x in results if ok]
        if not file_paths:
            update_item = {'notfound': 1}
            result = self.db.update_row(update_item, where_clause, db_table)
            raise DropItem("Item contains no files")

        item['file_paths'] = file_paths
        
        # Update download status `downloaded`   
        update_item = {'downloaded': 1}
        result = self.db.update_row(update_item, where_clause, db_table)
        
        return item

    def get_media_requests(self, item, info):
        item_headers = generate_headers(item['base_url'], 'image')
        for file_url in item['image_urls']:
            if file_url:                
                yield scrapy.Request(
                    file_url
                    , meta={'item': item} 
                    , headers=item_headers
                )

    def file_path(self, request, response=None, info=None):
        item = request.meta['item']
        return os.path.join(info.spider.name, item['rename'])

    """
    def file_path(self, request, response=None, info=None):
        file_path = super(DownloadImagePipeline, self).file_path(request, response, info)
        return os.path.join(info.spider.name, file_path[file_path.index('/') + 1:].split('?')[0])
    """

class ScrapyxFileExporterPipeline(object):
    pass

class ScrapyxDatabaseExporterPipeline(object):
    db = None
    def __init__(self):
        # Init DB connection
        self.db = Database()

    def process_item(self, item, spider):
        keys = item.keys()
        db_table = item['db_table']
        # Update item
        if 'is_update' in keys:            
            _item = item['item']

            if 'filter' in keys:
                where_clause = item['filter']
            else:
                pk_id = item['pk_id']
                pk_value = item['pk_value']            
                        
                if DB_TYPE == 'mongo':
                    where_clause = {str(pk_id): ObjectId(str(pk_value))}
                elif DB_TYPE == 'mysql':            
                    where_clause = u'{}={}'.format(pk_id, pk_value)
                elif DB_TYPE == 'postgres':
                    where_clause = u'"{}"={}'.format(pk_id, pk_value)
            
            result = self.db.update_row(_item, where_clause, db_table)
        # Insert items
        else:            
            if 'is_many' in keys:
                items = item['items']
                result = self.db.insert_multiple(items, db_table)
            else:
                _item = item['item']
                inserted_id = self.db.insert(_item, db_table)
                item.update({
                    'inserted_id': inserted_id
                    })
        return item

    def check_exist(self):
        pass

class ScrapyxUniqueFilterPipeline(object):
    """
    Filters duplicates using id field
    """
    seen = set()

    def process_item(self, item, spider):
        # If item has `id` attribute we check if it is already in `seen` list
        # and either drop it if already seen
        # or proceed and add its id to the `seen` list
        key_check = item.get('product_url', None)
        if key_check:
            if key_check in self.seen:
                raise DropItem()
            self.seen.add(key_check)
        return item
