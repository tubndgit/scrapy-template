# -*- coding: utf-8 -*-
import MySQLdb
import sys, json, time
import logging
from scrapy.utils.project import get_project_settings
from scrapyx.utils.utils import * 

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

settings = get_project_settings()

class Database(object): 
    db_config = []
    conn = None

    def __init__(self, params=None, *args, **kwargs):
        super(Database, self).__init__(*args, **kwargs)
        logging.info("Init MySQL")
        
        if params:
            self.db_config = params
        else:
            common_config = read_json('config/common.json')
            env = common_config['environment']    
            
            mysql_config = read_json('config/mysql.json')

            self.db_config = mysql_config[env]        

        if not self.conn:
            self.conn = self.init_connection()

    def init_connection(self):  
        conn = None 
        while True:            
            try:
                conn = MySQLdb.connect(user=self.db_config.get('DB_USER'), \
                    passwd=self.db_config.get('DB_PASS'), db=self.db_config.get('DB_NAME'), \
                    host=self.db_config.get('DB_HOST'), port=self.db_config.get('DB_PORT'), \
                    charset="utf8", use_unicode=True, connect_timeout=60)
                cursor = conn.cursor()
                break
            except Exception as e:
                logging.info("Try to connect failed")
                time.sleep(5)
                continue

        return conn
        
    def insert(self, item, db_table):
        #if not self.conn.open:
        #    self.conn = self.init_connection()

        try:
            self.conn.ping()
        except:
            self.conn = self.init_connection()

        cursor = self.conn.cursor()
        # Enforce UTF-8 for the connection.
        cursor.execute('SET NAMES utf8mb4')
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")

        aFormat = []                
        for key in item.keys():
            aFormat.append("%s")            
            
        sFormat = ', '.join(aFormat)
        
        fields = ', '.join(item.keys())
        insert_id = 0
        try:
            cursor.execute("""INSERT INTO """ + db_table + """(""" + fields + """)  
                            VALUES (""" + sFormat + """)""", 
                           item.values())
            insert_id = self.conn.insert_id()
            self.conn.commit()
        except MySQLdb.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            self.conn.rollback()
          
        return insert_id

    def insert_multiple(self, data, table_name):
        #if not self.conn.open:
        #    self.conn = self.init_connection()

        try:
            self.conn.ping()
        except:
            self.conn = self.init_connection()

        cursor = self.conn.cursor()
        # Enforce UTF-8 for the connection.
        cursor.execute('SET NAMES utf8mb4')
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")

        aFormat = []        

        sColumns = ', '.join(data[0].keys())

        for key in data[0].keys():
          aFormat.append("%s")            
        sFormat = ', '.join(aFormat)    

        values_to_insert = [x.values() for x in data]
        
        _return = False
        try:           
            _query = "INSERT INTO " + table_name + "(" + sColumns + ") VALUES " + ",".join("(" + sFormat + ")" for _ in values_to_insert)
            flattened_values = [item for sublist in values_to_insert for item in sublist]
            cursor.execute(_query, flattened_values)

            #args_str = ','.join(cursor.mogrify("(" + sFormat + ")", x.values()) for x in data)
            #result = cursor.execute("INSERT INTO " + table_name + "(" + sColumns + ") VALUES " + args_str)       
       
        except MySQLdb.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            self.conn.rollback()
            _return = False
        finally:
          self.conn.commit()
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
                #value = value.replace('"', '\\"')
                #_supdate = u'{} = "{}"'.format(k, value)
                value = item[k].replace("'", "\\'")
                _supdate = u"{} = '{}'".format(k, value)
            else:                
                _supdate = u'{} = {}'.format(k, value)                                
            aUpdate.append(_supdate)
        
        sUpdate = u', '.join([u'{}'.format(x) for x in aUpdate])

        query_update = u'UPDATE {} SET {} WHERE {}'.format(db_table, sUpdate, where_clause)    

        result = self.exec_query(query_update)
        return result
        
    def exec_query(self, query):
        #if not self.conn.open:
        #    self.conn = self.init_connection()

        try:
            self.conn.ping()
        except:
            self.conn = self.init_connection()

        cursor = self.conn.cursor()
        # Enforce UTF-8 for the connection.
        cursor.execute('SET NAMES utf8mb4')
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")

        try:
            result = cursor.execute(query)        
            self.conn.commit()
            return result
        except MySQLdb.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))
            self.conn.rollback()
            return False
            
    def select(self, query):
        #if not self.conn.open:
        #    self.conn = self.init_connection()

        try:
            self.conn.ping()
        except:
            self.conn = self.init_connection()
            
        cursor = self.conn.cursor() 
        # Enforce UTF-8 for the connection.
        cursor.execute('SET NAMES utf8mb4')
        cursor.execute("SET CHARACTER SET utf8mb4")
        cursor.execute("SET character_set_connection=utf8mb4")
        
        try:
            cursor.execute(query)
            #rows = cursor.fetchall()
            columns = cursor.description 
            rows = [{columns[index][0]:column for index, column in enumerate(value)} for value in cursor.fetchall()]
            return rows
        except MySQLdb.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))        
            return False
    
    def get_columns(self, db_table):
        #if not self.conn.open:
        #    self.conn = self.init_connection()

        try:
            self.conn.ping()
        except:
            self.conn = self.init_connection()
            
        cursor = self.conn.cursor()
        try:
            _query = "SHOW columns FROM {}".format(db_table)
            cursor.execute(_query)
            return [column[0] for column in cursor.fetchall()]
        except MySQLdb.Error as e:
            print ("Error %d: %s" % (e.args[0], e.args[1]))        
            return False