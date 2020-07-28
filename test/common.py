# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

"""
HOW TO USE

------------------------------------------------------------
# CSV 
python test/common.py --csv read
python test/common.py --csv write

------------------------------------------------------------
# Domain/URL

# Get domain
python test/common.py --domain https://www.google.com

# Get url params
python test/common.py --parse_url "https://unsplash.com/napi/search/photos?query=landscape&xp=&per_page=30&page=1"

------------------------------------------------------------
# Get emails from text
python test/common.py --email "afd aaaa@fdasf-com.com fadsf"

------------------------------------------------------------
# Get phones from text
python test/common.py --phone "rong>Penang:</strong> + 60 (0)4 255 9000</p>"

------------------------------------------------------------
# Get links from text
python test/common.py --link "<p>Contents :</p><a href="https://w3resource.com">Python Examples</a><a href="http://github.com">Even More Examples</a>"

------------------------------------------------------------
# Cookies
python test/common.py --cookie_str "Cookie: devicePixelRatio=1; ident=exists; __utma=13103r6942.2918; __utmc=13103656942; __utmz=13105942.1.1.1.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); mp_3cb27825a6612988r46d00tinct_id%22%3A%201752338%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fwww.pion_created_at%22%3A%20%222015-08-03%22%2C%22platform%22%3A%20%22web%22%2C%%22%3A%20%%22%7D; t_session=BAh7DUkiD3Nlc3NpbWVfZV9uYW1lBjsARkkiH1BhY2lmaWMgVGltZSAoVVMgJiBDYW5hZGEpBjsAVEkiFXNpZ25pbl9wZXJzb25faWQGOwBGaQMSvRpJIhRsYXN0X2xvZ2luX2RhdGUGOwBGVTogQWN0aXZlU3VwcG9ydDo6VGltZVdpdGhab25lWwhJdToJVGltZQ2T3RzAAABA7QY6CXpvbmVJIghVVEMGOwBUSSIfUGFjaWZpZWRfZGFzaGJvYXJkX21lc3NhZ2UGOwBGVA%3D%3D--6ce6ef4bd6bc1a469164b6740e7571c754b31cca"

python test/common.py --cookie_str "set-cookie: SIDCC=AJi4QfHskU5ksE7mMllySFcDcVy3ZPG9ZZhKgJ93UloJoaNCIFME8LALl4jABfZ99mPoAbohBH0; expires=Thu, 25-Mar-2021 03:48:01 GMT; path=/; domain=.google.com; priority=high"

------------------------------------------------------------
# Test sending mail

python test/common.py --mail m

------------------------------------------------------------
# Test replace string

python test/common.py --rpl r

------------------------------------------------------------
# Test Excel
# Excel to json
python test/common.py --excel read json

# Excel to CSV
python test/common.py --excel read csv

# CSV to Excel
python test/common.py --excel write csv

# JSON to Excel
python test/common.py --excel write json

"""
import os, sys
from scrapy.crawler import CrawlerProcess
import boto3
from scrapy.utils.project import get_project_settings
import argparse
import tldextract
import string, json
from collections import OrderedDict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scrapyx.utils.utils import * 
from pprint import pprint

def test(args):
    if args.csv:
        params = args.csv
        if params[0] == 'read':
            data = read_csv('output/csv/test.csv')
            for d in data:
                print(d)

        if params[0] == 'write':
            data = [{'k1': 'v1', 'k2': 'v2'}, {'k1': 'v11"', 'k2': 'v22'}]
            write_csv(data, 'output/csv/test.csv')

    if args.domain:
        params = args.domain
        url = params[0]
        domain = get_domain(url)
        print("Domain: %s" % domain)

        c = slugify_url(url)
        print("Slug: %s" % c)

    if args.email:
        params = args.email
        text = params[0]
        emails = get_emails(text)
        print(emails)

    if args.phone:
        params = args.phone
        text = params[0]
        phones = get_phones(text)
        print(phones)

    if args.link:
        params = args.link
        text = params[0]
        links = get_links(text)
        print(links)

    if args.cookie:
        params = args.cookie
        cookie = params[0]
        cookies = parse_cookie(cookie)
        print(cookies)

    if args.cookie_str:
        params = args.cookie_str
        cookie = params[0]
        cookies = parse_cookie_str(cookie)
        print(cookies)

    if args.mail:
        sendAlert()

    if args.rpl:
        text = u'how are you doing?'
        print("Original string: ", text)

        search_list = [u'how', 'you']
        rpl_list = ['What', u'they']
        r_text = repl(search_list, rpl_list, text)
        print("Filnal string: ", r_text)

    if args.parse_url:        
        params = args.parse_url
        url = params[0]        
        params = get_url_params(url)
        print(params)

    if args.excel:
        params = args.excel
        print(params)
        if params[0] == 'read':
            # Excel to json
            if params[1] == 'json':
                # Write to file
                #a = excel_to_json('output/csv/input.xlsx', 'Sheet1', 'output/csv/excel_to_json.json')
                # Return json data
                a = excel_to_json('output/csv/input.xlsx', 'Sheet1')
                pprint(a)
            # Excel to csv
            if params[1] == 'csv':
                excel_to_csv('output/csv/input.xlsx', 'output/csv/excel_to_csv.csv')

        if params[0] == 'write':
            # csv to excel
            if params[1] == 'csv':
                csv_to_excel('output/csv/test.csv', 'output/csv/csv_to_excel.xlsx')
            # json to excel
            if params[1] == 'json':
                json_data = [{'k1': 'v1', 'k2': 'v2'}, {'k1': 'v11"', 'k2': 'v22'}, {'k1': 'Lê Minh Thắng', 'k2': 'Trần Thị Hồng Hạnh'}]
                json_to_excel(json_data, 'output/csv/json_to_excel.xlsx')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command lines')
    parser.add_argument('--csv', metavar='path', required=False, nargs='+', 
                        help="Test csv's read/write functions")

    parser.add_argument('--domain', metavar='path', required=False, nargs='+', 
                        help="Get domain from url")

    parser.add_argument('--email', metavar='path', required=False, nargs='+', 
                        help="Get emails from text")

    parser.add_argument('--phone', metavar='path', required=False, nargs='+', 
                        help="Get phones from text")

    parser.add_argument('--link', metavar='path', required=False, nargs='+', 
                        help="Get links from text")

    parser.add_argument('--cookie', metavar='path', required=False, nargs='+', 
                        help="Parse cookies")

    parser.add_argument('--cookie_str', metavar='path', required=False, nargs='+', 
                        help="Parse string cookies")

    parser.add_argument('--mail', metavar='path', required=False, nargs='+', 
                        help="Test send mail")

    parser.add_argument('--rpl', metavar='path', required=False, nargs='+', 
                        help="Test replace string")

    parser.add_argument('--excel', metavar='path', required=False, nargs='+', 
                        help="Test excel")

    parser.add_argument('--parse_url', metavar='path', required=False, nargs='+', 
                        help="Get url params")

    args = parser.parse_args()    
    test(args)