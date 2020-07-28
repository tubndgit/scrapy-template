# -*- coding: utf-8 -*-

from __future__ import print_function
#import httplib2
import os

#from apiclient import discovery
#from oauth2client import client
#from oauth2client import tools
#from oauth2client.file import Storage
from pprint import pprint
import logging
import sys
import psycopg2
import json
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
from scrapyx.utils.utils import * 

__author__ = 'Henry B. <tubnd.younet@gmail.com>'
  
class Database(object): 
    settings = []
    connection = None 
  
    def __init__(self, params=None, *args, **kwargs):
        super(Database, self).__init__(*args, **kwargs)
        logging.info("Init Postgres")     
        
        if params:
            self.settings = params
            self.schema = params['postgres_schema']
        else:
            common_config = read_json('config/common.json')
            env = common_config['environment'] 
        
            _config = read_json('config/postgres.json')
            config = _config[env]          
            self.settings = config
            self.schema = config['postgres_schema']

        if not self.connection:
            self.connection = self.init_connection()
      
    def init_connection(self):    
        # connect to postgres
        connection = psycopg2.connect(
                database=self.settings.get('postgres_database'),
                user=self.settings.get('postgres_username'),                
                password=self.settings.get('postgres_password'),
                host=self.settings.get('postgres_host'),
                port=self.settings.get('postgres_port'),
                options='-c search_path={}'.format(self.schema)
              )
    
        return connection
    
    def insert(self, data, table_name):
        if not self.connection.status:
            self.connection = init_connection()

        cursor = self.connection.cursor()
        aFormat = []        

        sColumns = '", "'.join(data.keys())

        for key in data.keys():
            aFormat.append("%s")            
        sFormat = ', '.join(aFormat)    

        result = False
    
        try:      
            query_string = "INSERT INTO {} (\"{}\") VALUES({})".format(table_name, sColumns, sFormat)
          
            xresult = cursor.execute(query_string, list(data.values()))
            cursor.execute('SELECT LASTVAL()')
            #cursor.execute()
            result = cursor.fetchone()[0]      
        except Exception as e:
            print(e)
        except psycopg2.DatabaseError as e:
            logging.info("DatabaseError: %s", e)
            self.connection.rollback()     
        except psycopg2.InterfaceError as exc:  
            logging.info("InterfaceError: %s", exc)
            self.connection = self.init_connection()
            cursor = self.connection.cursor()
        finally:
            self.connection.commit()  

        return result

    def insert_multiple(self, data, table_name):
        if not self.connection.status:
            self.connection = self.init_connection()
      
        cursor = self.connection.cursor()

        aFormat = []        

        sColumns = '", "'.join(data[0].keys())

        for key in data[0].keys():
            aFormat.append("%s")            
        sFormat = ', '.join(aFormat)    

        values_to_insert = [x.values() for x in data]
    
        _return = False
        try:              
            #args_str = ','.join(cursor.mogrify("(" + sFormat + ")", list(x.values())) for x in data)
            #result = cursor.execute("INSERT INTO " + table_name + "(\"" + sColumns + "\") VALUES " + args_str)    

            _query = "INSERT INTO " + table_name + "(\"" + sColumns + "\") VALUES " + ",".join("(" + sFormat + ")" for _ in values_to_insert)
            flattened_values = [item for sublist in values_to_insert for item in sublist]
            cursor.execute(_query, flattened_values)
       
        except psycopg2.DatabaseError as e:
            logging.info("DatabaseError: %s", e)
            self.connection.rollback()     
        except psycopg2.InterfaceError as exc:  
            logging.info("InterfaceError: %s", exc)
            self.connection = self.init_connection()
            cursor = self.connection.cursor()
        finally:
            self.connection.commit()
            _return = True

        return _return

    def update_row(self, item, where_clause, db_table):        
        aUpdate = []
        keys = item.keys()
        for k in keys:                    
            value = item[k]  
            py_ver = sys.version_info[0]      
            if py_ver > 2:
                str_inst = str
            else:
                str_inst = basestring

            if isinstance(value, str_inst):                                                           
                value = value.replace("'", "''")
                _supdate = u'"{}" = \'{}\''.format(k, value)
            else:                
                _supdate = u'"{}" = {}'.format(k, value)                               
            aUpdate.append(_supdate)
        
        sUpdate = u', '.join([u'{}'.format(x) for x in aUpdate])

        query_update = u'UPDATE {} SET {} WHERE {}'.format(db_table, sUpdate, where_clause)    
        result = self.exec_query(query_update)
        return result

    def exec_query(self, query):
        if not self.connection.status:
            self.connection = init_connection()
        
        result = False
        cursor = self.connection.cursor()    
        try:
            result = cursor.execute(query)      
            return result
        except psycopg2.DatabaseError as e:
            logging.info("DatabaseError: %s", e)
            self.connection.rollback()
            return False
        finally:
            self.connection.commit()
            result = True        

        return result    
    
    def select(self, query):
        if not self.connection.status:
            self.connection = init_connection()
          
        cursor = self.connection.cursor()
        
        try:
            cursor.execute(query)
            #rows = cursor.fetchall()
            columns = cursor.description 
            rows = [{columns[index][0]:column for index, column in enumerate(value)} for value in cursor.fetchall()]
            return rows
        except psycopg2.DatabaseError as e:
            logging.info("DatabaseError: %s", e)
            self.connection.rollback()
            return False

    def get_columns(self, db_table):
        if not self.connection.status:
            self.connection = init_connection()
          
        cursor = self.connection.cursor()
        try:
            _query = "SELECT * FROM {} LIMIT 0".format(db_table)
            cursor.execute(_query)
            colnames = [desc[0] for desc in cursor.description]
            return colnames
        except psycopg2.DatabaseError as e:
            logging.info("DatabaseError: %s", e)
            self.connection.rollback()
            return False
    