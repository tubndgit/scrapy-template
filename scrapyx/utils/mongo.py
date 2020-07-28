# -*- coding: utf-8 -*-
from pymongo import MongoClient
from scrapy.exceptions import DropItem
import logging
import json
from bson.objectid import ObjectId
from scrapyx.utils.utils import * 

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

class Database(object):
	settings = []
	connection = None

	def __init__(self, params=None, *args, **kwargs):
		super(Database, self).__init__(*args, **kwargs)
		logging.info("Init MongoDB")
		
		if params:
			self.settings = params
		else:
			common_config = read_json('config/common.json')
			env = common_config['environment'] 
			
			_mongo_config = read_json('config/mongo.json')
			mongo_config = _mongo_config[env]          
			self.settings = mongo_config   

		if not self.connection:
			self.connection = self.init_connection()   

	def init_connection(self):              
		srv = self.settings['srv']
		try:
			if self.settings['host'] == 'localhost':
				connection = MongoClient(
					self.settings['host'],
					self.settings['port']
				)
			else:
				if srv:
					connection = MongoClient('mongodb+srv://{}:{}@{}/{}'.format(\
						self.settings['user'], self.settings['password'], \
						self.settings['host'], self.settings['admin_database']))
				else:
					connection = MongoClient('mongodb://{}:{}@{}:{}/{}'.format(\
						self.settings['user'], self.settings['password'], \
						self.settings['host'], self.settings['port'], self.settings['admin_database']))        
					
			db = connection[self.settings['database']]			
			return db
		except Exception as e:
			logging.error('Cannot connect to MongoDB...')
			logging.error(e)
			return False

	def insert(self, item, coll):		
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]		

		valid = True
		for data in item:
			if not data:
				valid = False
				raise DropItem("Missing {0}!".format(data))
		if valid:
			try:
				inserted_id = collection.insert_one(dict(item)).inserted_id
				logging.info("Data added to MongoDB database!")   
				return inserted_id
			except Exception as e:
				logging.error(e)
				return False

	def insert_multiple(self, data, coll):
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]		

		try:
			inserted_ids = collection.insert_many(data).inserted_ids
			logging.info("Data added to MongoDB database!")   
			return inserted_ids
		except Exception as e:
			logging.error(e)
			return False		

	def update_row(self, item, query, coll):
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]

		try:
			result = collection.update_many(query, {"$set": item})
			logging.info("Data Updated!")   
			return result.modified_count
		except Exception as e:
			logging.error(e)
			return False

	def select(self, query, coll, limit=None):
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]

		try:			
			if limit:
				results = collection.find(query).limit(int(limit))
			else:
				results = collection.find(query)
			logging.info("Query success!")   
			return results
		except Exception as e:
			logging.error(e)
			return False

	def delete(self, query, coll):
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]

		try:
			result = collection.delete_many(query).deleted_count
			logging.info("Delete success!")   
			return result
		except Exception as e:
			logging.error(e)
			return False

	def get_columns(self, coll):
		if not self.connection:
			self.connection = self.init_connection()

		collection = self.connection[coll]

		try:			
			row = collection.find_one()
			logging.info("Query success!")   
			return row.keys()
		except Exception as e:
			logging.error(e)
			return False