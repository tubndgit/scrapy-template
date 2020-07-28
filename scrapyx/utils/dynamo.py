# -*- coding: utf-8 -*-
from __future__ import print_function # Python 2/3 compatibility
import logging
from scrapy.utils.project import get_project_settings
from scrapyx.utils.utils import * 

import boto3
import json
import decimal
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

settings = get_project_settings()

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

class Database(object): 
    db_config = []
    conn = None

    def __init__(self, *args, **kwargs):
        super(Database, self).__init__(*args, **kwargs)
        logging.info("Init DynamoDB")
        
        common_config = read_json('config/common.json')
        env = common_config['environment']    
        
        dynamo_config = read_json('config/dynamo.json')
        self.db_config = dynamo_config[env]        

        if not self.conn:
            self.conn = self.init_connection()

    def init_connection(self):   
        conn = boto3.resource('dynamodb', 
            region_name=self.db_config['region_name'], 
            endpoint_url=self.db_config['endpoint_url'])

        return conn

    def Table(self, tbl):
        return self.conn.Table(tbl)
        
    def insert(self, item, db_table):
        if not self.conn:
            self.conn = self.init_connection()

        table = self.Table(db_table)

        response = table.put_item(
           Item=item
        )

        print("PutItem succeeded")
        print(json.dumps(response, indent=4, cls=DecimalEncoder))

    def insert_multiple(self, data, table_name):
        if not self.conn:
            self.conn = self.init_connection()

        table = self.Table(table_name)

        with table.batch_writer() as batch:
            for r in data:
                batch.put_item(Item=r)
                print("PutItem succeeded")

    def update_row(self, item, where_clause, db_table):        
        if not self.conn:
            self.conn = self.init_connection()

        pass
        
    def exec_query(self, query):
        if not self.conn:
            self.conn = self.init_connection()

        pass
            
    def select(self, query):
        if not self.conn:
            self.conn = self.init_connection()

        pass
    
    def get_columns(self, db_table):
        if not self.conn:
            self.conn = self.init_connection()

        table = self.Table(db_table)
        result = table.scan(Limit=1)
        return result['Items'][0].keys()