# -*- coding: utf-8 -*-
from __future__ import print_function
import zipfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotVisibleException
import time
import json, re, os, string, csv
import random
import base64
from selenium.webdriver.common.proxy import *
from scrapy.selector import Selector

from scrapy.utils.project import get_project_settings
from fake_useragent import UserAgent

import smtplib
import tldextract
import hashlib
import os.path
from pprint import pprint
#from http.cookies import SimpleCookie
import pandas as pd
from datetime import datetime, timedelta

try:
    from urllib.parse import urlparse, unquote
except ImportError:
     from urlparse import urlparse, unquote

__author__ = 'Henry B. <tubnd.younet@gmail.com>'

settings = get_project_settings()
#print(settings.get('FEED_EXPORT_FIELDS'))

""" ----------------------------------------------------------------------------
Read file content
"""
def read_file(file_path):
    with open(file_path, "r") as f:
        content = f.read()
        f.close()
    return content

""" Write content to file"""
# type: w --> over-written
# type: a --> append

def write_file(content, file_path, type='w'):
    with open(file_path, type) as f:
        f.write(content)
        f.close()

def read_lines(file_path, type='r'):
    lines = []
    with open(file_path, type) as f:
        lines = [line.rstrip() for line in f]
        f.close()
    return lines

""" ----------------------------------------------------------------------------
Read json file and return json data
"""
def read_json(json_file):
    json_data = None
    try:
        content = read_file(json_file)
        json_data = json.loads(content)        
    except Exception as e:
        print(e)
    
    return json_data

""" Write json data to file"""
def write_json(data, json_file):
    with open(json_file, 'w') as f:
        json.dump(data, f, ensure_ascii=True, indent=4)
        f.close()

""" ----------------------------------------------------------------------------
Read data from csv
Return list [{'k1': v1, 'k2': v2}, {'k1': v1, 'k2': v2}]
"""
def read_csv(csv_file, delimiter=',', quote='"', headers=True):    
    fieldnames = []
    f = open(csv_file, "r")
    if headers:
        reader = csv.DictReader(f)
    else:
        pass
    return reader

"""
Write data to csv
Input: list [{'k1': v1, 'k2': v2}, {'k1': v1, 'k2': v2}]
"""
def write_csv(data, csv_file, fieldnames=None, delimiter=',', quote='"'):
    f = open(csv_file, "wb")
    if not fieldnames:
        fieldnames = data[0].keys()
    writer = csv.DictWriter(f, 
        fieldnames=fieldnames, 
        delimiter=delimiter,
        quotechar=quote,
        quoting=csv.QUOTE_ALL)
    writer.writeheader()
    for item in data:
        writer.writerow(item)
    f.close()

""" ----------------------------------------------------------------------------
Read config file
"""
_config = read_json('config/common.json')
env = _config['environment']
common_config = _config[env]

_mail_config = read_json('config/mail.json')
mail_config = _mail_config[env]

_proxy_config = read_json('config/proxy.json')
proxy_config = _proxy_config[env]

""" ----------------------------------------------------------------------------
Functions for Selenium
"""
driver = None

def init_web_driver(proxyOpt = None):   
    global driver 
    
    # Firefox
    if proxyOpt == 1:
        driver = webdriver.Firefox()

    # Chrome
    elif proxyOpt == 2:
        chromeOptions = webdriver.ChromeOptions()   
        prefs = {"download.default_directory" : common_config['download_folder']}
        chromeOptions.add_experimental_option("prefs",prefs)  
        #chromeOptions.add_argument("--start-maximized") 
        
        path_to_chromedriver = common_config['path_to_chromedriver'] # change path as needed
        driver = webdriver.Chrome(executable_path = path_to_chromedriver, chrome_options=chromeOptions)

    return driver

def close_web_driver():
    if driver:
        driver.close()

""" Wait for element """
def wait_for_element(driver, selector, timeout=10):
    try:
        wait = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR , selector))
            )   

        return driver.find_element_by_css_selector(selector)
    except:
        print ('Element with selector "%s" not visible' % selector)
        return False

""" Wait for element xpath"""
def wait_for_element_xpath(driver, xpath, timeout=10):  
    try:
        wait = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH , xpath))
            )    

        return driver.find_element_by_xpath(xpath)
    except:
        print ('Element with xpath "%s" not visible' % xpath)
        return False

""" 
Generate Selector from text
"""
def gen_selector(content):
    sel = Selector(text=content, type="html")
    return sel
            
""" ----------------------------------------------------------------------------
Sending mail 
"""
def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    header = 'From: %s' % from_addr
    header += '\nTo: %s' % ','.join(to_addr_list)
    if len(cc_addr_list):
        header += '\nCc: %s' % ','.join(cc_addr_list)
    header += '\nSubject: %s' % subject
    message = header + message
             
    server = smtplib.SMTP(smtpserver)
    #server = smtplib.SMTP_SSL(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()
    
def sendAlert(params):       
    if common_config['email_alert'] == 1:
        to_addr_list = []
        for x in mail_config["to_addr_list"]:
            if x[0] == '#':
                continue
            to_addr_list.append(x)
        if not to_addr_list:
            return

        cc_addr_list = []
        for x in mail_config["cc_addr_list"]:
            if x[0] == '#':
                continue
            cc_addr_list.append(x)

        login = mail_config['user']
        passwd =  mail_config['pass']

        sub = params['sub']
        msg = params['msg']
        
        if sub == None:            
            _subject = common_config['machine'] + " - " + mail_config["subject"]      
        else:
            _subject = sub  

        if msg == None:
            _message = "\n\n{}".format(mail_config["message"])
        else:
            _message = '\n\n{}'.format(msg)            

        sendemail(
            from_addr = mail_config['user'], 
            to_addr_list = to_addr_list, 
            cc_addr_list = cc_addr_list,
            subject = _subject, 
            message = _message,                
            login = login,
            password = passwd
        )
    else:
        pass

""" ----------------------------------------------------------------------------
Genetate headers from template 
"""
def generate_headers(base_url, header_type=None):
    if not header_type:
        return {}
    if header_type == 'ajax':
        header_tpl = 'templates/headers_ajax.tpl'
    elif header_type == 'image':
        header_tpl = 'templates/headers_image.tpl'
    else:
        header_tpl = 'templates/headers.tpl'

    header_content = read_file(header_tpl)
            
    _header_content = header_content.replace('{BASE_URL}', base_url)    

    return json.loads(_header_content)

""" ----------------------------------------------------------------------------
Check if proxy enable ot not
"""
def is_proxy_enabled():
    proxy = common_config['proxy']        
    PROXY_ENABLED = False
    if proxy:
        PROXY_ENABLED = True

    return PROXY_ENABLED

# Get proxy URL
def get_proxy_url():
    proxy = common_config['proxy']
    if not proxy:
        return ''
    choose = str(proxy)
    PROXY_URL = proxy_config['proxy_url'][choose]

    return PROXY_URL

""" ---------------------------------------------------------------------------- 
Feed export
"""
def get_item_piplines():
    is_download = common_config['download']
    feed_format = common_config['feed_format']

    ITEM_PIPELINES = {'scrapyx.pipelines.ScrapyxUniqueFilterPipeline': 200}

    # Download image, don't update database
    if is_download == 1:
        ITEM_PIPELINES.update({                              
            'scrapyx.pipelines.ScrapyxDownloadImagePipeline': 300
        })
        
    # Download image, update database
    if is_download == 2:
        ITEM_PIPELINES.update({                                
            'scrapyx.pipelines.ScrapyxDownloadImageFromDatabasePipeline': 300
        })
    
    if feed_format in ['db'] and not is_download:
        ITEM_PIPELINES.update({                                
            'scrapyx.pipelines.ScrapyxDatabaseExporterPipeline': 300
        })

    if feed_format in ['csv', 'json', 'xml'] and not is_download:
        ITEM_PIPELINES.update({                                
            'scrapyx.pipelines.ScrapyxFileExporterPipeline': 300
        })

    return ITEM_PIPELINES

""" ----------------------------------------------------------------------------
Return first number that found in string
"""
def get_1st_number_from_st(text, min_dig='1', max_dig='', add_char=','):    
    if not text:
        return ''    
    pattern = "\d+([,|.]\d{{{}}})*([,|.]\d{{{},{}}})?".format('3', min_dig, max_dig)
    try:
        return re.search(pattern, text).group()
    except AttributeError:
        return ''

""" ----------------------------------------------------------------------------
Get domain from url
"""
def get_domain(url):        
    extracted_url = tldextract.extract(url)       
    domain_name = extracted_url.domain + '.' + extracted_url.suffix
    return domain_name

re_schema = re.compile(r'^.+?//')
re_slug = re.compile(r'[.#&=?/\-+]+')

def slugify_url(url):
    return re_slug.sub('_', re_schema.sub('', url))

def decode_url(url):
    original_url = unquote(url)
    return original_url

def get_url_params(url):
    params = {}
    url = decode_url(url)
    url_params = url.split('?')[-1]
    url_params_part = url_params.split('&')
    for x in url_params_part:
        params_part = x.split('=')
        if len(params_part) == 2:
            params[params_part[0]] = params_part[1]
    return params

def parse_cookie_draft(rawdata):
    #rawdata = 'Cookie: devicePixelRatio=1; ident=exists; __utma=13103r6942.2918; __utmc=13103656942; __utmz=13105942.1.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); mp_3cb27825a6612988r46d00tinct_id%22%3A%201752338%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.pion_created_at%22%3A%20%222015-08-03%22%2C%22platform%22%3A%20%22web%22%2C%%22%3A%20%%22%7D; t_session=BAh7DUkiD3Nlc3NpbWVfZV9uYW1lBjsARkkiH1BhY2lmaWMgVGltZSAoVVMgJiBDYW5hZGEpBjsAVEkiFXNpZ25pbl9wZXJzb25faWQGOwBGaQMSvRpJIhRsYXN0X2xvZ2luX2RhdGUGOwBGVTogQWN0aXZlU3VwcG9ydDo6VGltZVdpdGhab25lWwhJdToJVGltZQ2T3RzAAABA7QY6CXpvbmVJIghVVEMGOwBUSSIfUGFjaWZpZWRfZGFzaGJvYXJkX21lc3NhZ2UGOwBGVA%3D%3D--6ce6ef4bd6bc1a469164b6740e7571c754b31cca'
    cookie = SimpleCookie()
    cookie.load(rawdata)

    # Even though SimpleCookie is dictionary-like, it internally uses a Morsel object
    # which is incompatible with requests. Manually construct a dictionary instead.
    cookies = {}
    for key, morsel in cookie.items():
        cookies[key] = morsel.value
    return cookies

def parse_cookie_str(cookiestr):
    cookies = {}
    cookiestr = cookiestr.replace('Cookie: ', '').replace('set-cookie: ', '')
    rawdata_split = cookiestr.split(';')
    for x in rawdata_split:
        key_val = x.split('=')
        if len(key_val) > 1:
            cookies[key_val[0]] = key_val[1].strip()
    return cookies

def parse_cookie(response):
    cookies = {}
    rawdata = response.headers.getlist('Set-Cookie')[0]    
    if isinstance(rawdata, bytes):
        rawdata = rawdata.decode()
    rawdata_split = rawdata.split(';')
    for x in rawdata_split:
        key_val = x.split('=')
        if len(key_val) > 1:
            cookies[key_val[0]] = key_val[1].strip()
    return cookies

""" ----------------------------------------------------------------------------
STRING
"""
def md5(text):
    md5hash = hashlib.md5(text).hexdigest()
    return md5hash

def get_js(response, key):
    script_text = response.xpath(u'.//script[contains(text(),"{}")]//text()'.format(key)).get('')
    #script_text = ' '.join([x.strip() for x in script_text.replace('\n', '').split(' ') if x.strip()])
    return script_text

def rename_file(url, ext=None):
    url_part = url.split('?')
    if not ext:
        ext = url_part[0].split('.')[-1]
    fname = u'{}.{}'.format(md5(url), ext)
    return fname

# Replace text with list searching string
# text =  u'how are you doing?'
# search_list = [u'how', 'you']
# rpl_list = ['What', u'they']
# r_text = rpl(search_list, rpl_list, text)
# print(r_text)
# ==> u'What are they doing?'

def repl(search_list, rpl_list, text):
    for i, x in enumerate(search_list):
        text = text.replace(x, rpl_list[i])
    return text

""" ----------------------------------------------------------------------------
Regular expression
"""
def regx(key, content):
    pattern = re.compile(r'{}'.format(key))
    matches = pattern.findall(content)    
    return matches    

def get_emails(text):
    rgx = r'(?:\.?)([\w\-_+#~!$&\'\.]+(?<!\.)(@|[ ]?\(?[ ]?(at|AT)[ ]?\)?[ ]?)(?<!\.)[\w]+[\w\-\.]*\.[a-zA-Z-]{2,3})(?:[^\w])'    
    matches = re.findall(rgx, text)
    get_first_group = lambda y: list(map(lambda x: x[0], y))
    emails = get_first_group(matches)
    return emails

def get_phones(text):
    rgx = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'    
    matches = re.findall(rgx, text)
    return matches

def get_links(text):    
    rgx = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:\'\".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
    matches = re.findall(rgx, text)
    return matches

""" ----------------------------------------------------------------------------
List / Dict

TODO

"""


""" ----------------------------------------------------------------------------
Working with Excel
"""

def excel_to_csv(excel_file, csv_file, sheet_name='Sheet1', index_col=None):
    data_xls = pd.read_excel(excel_file, sheet_name, index_col=index_col)
    data_xls.to_csv(csv_file, encoding='utf-8')

def csv_to_excel(csv_file, excel_file, sheet_name='Sheet1', index=False):
    # index: First column with index 1, 2, 3, 4...
    pd.read_csv(csv_file).to_excel(excel_file, sheet_name=sheet_name, index=index, encoding='utf-8')

def excel_to_json(excel_file, sheet_name='Sheet1', output_file=None):
    data_xls = pd.read_excel(excel_file, sheet_name, index_col=None)
    if output_file:
        data_xls.to_json(output_file, orient='records')
    else:        
        json_data = data_xls.to_json(orient='records')
        return json.loads(json_data)

def json_to_excel(json_data, excel_file, sheet_name='Sheet1', index=False):    
    df = pd.DataFrame.from_dict(json_data)
    df.to_excel(excel_file, sheet_name=sheet_name, index=index, encoding='utf-8')

""" ----------------------------------------------------------------------------
TODO
"""


if __name__ == '__main__':
    pass    