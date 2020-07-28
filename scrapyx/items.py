# -*- coding: utf-8 -*-
import six
import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import *

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

# Items documentation: https://doc.scrapy.org/en/latest/topics/items.html
class BaseItem(scrapy.Item):
    """
    id          - unique product id, used for duplicate filtering
    """
    #id = scrapy.Field()
    biz_id = scrapy.Field()
    thumbnail = scrapy.Field()    
        
# Item Loaders documentation: https://doc.scrapy.org/en/latest/topics/loaders.html
# Concept of item loader is very helpful as it allows to separate parsing and data processing
class BaseItemLoader(ItemLoader):
    default_item_class = BaseItem
    default_output_processor = Compose(TakeFirst(), six.text_type, six.text_type.strip)

    def load_item(self, *args, **kwargs):
        item = super(BaseItemLoader, self).load_item(*args, **kwargs)
        # Populate alternative_image_url_xx columns with one url per column
        for i, u in enumerate(item.get('image_urls', [])[:15], 1):
            item['alternative_image_url_%s' % i] = u
        return item

# Define other Items below