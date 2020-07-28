# -*- coding: utf-8 -*-
__author__ = 'Henry B. <tubnd.younet@gmail.com>'

"""
HOW TO USE

python database/pg_setup.py

"""

import json, sys, os
import argparse
from pprint import pprint
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scrapyx.utils.utils import * 
from scrapyx.utils.postgres import *

common_config = read_json('config/common.json')
env = common_config['environment']    

_postgres_db_config = read_json('config/postgres.json')
postgres_db_config = _postgres_db_config[env]    
DB_SCHEMA = postgres_db_config['postgres_schema']

# Init postgre connection
oDb = Database()

# Create table
TABLE_NAME = 'categories'
SEQUENCE_NAME = 'categories_id_seq'

create_tbl_query = """
CREATE TABLE DB_SCHEMA.TABLE_NAME
(
    id integer NOT NULL,
    name_en text COLLATE pg_catalog."default" NOT NULL,
    name_th text COLLATE pg_catalog."default" NOT NULL,
    level integer NOT NULL,
    is_child boolean,
    parent_id integer,
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),
    icon text COLLATE pg_catalog."default",
    status boolean,
    description_en text COLLATE pg_catalog."default",
    description_th text COLLATE pg_catalog."default",
    merchant_id text COLLATE pg_catalog."default",
    CONSTRAINT categories_pkey PRIMARY KEY (id),
    CONSTRAINT categories_id_key UNIQUE (id)
,
    CONSTRAINT categories_parent_id_fkey FOREIGN KEY (parent_id)
        REFERENCES DB_SCHEMA.TABLE_NAME (id) MATCH SIMPLE
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;"""


create_tbl_query = create_tbl_query.replace('DB_SCHEMA', DB_SCHEMA).replace('TABLE_NAME', TABLE_NAME)
    
drop_tbl_query = "DROP TABLE IF EXISTS {}.{} CASCADE;".format(DB_SCHEMA, TABLE_NAME)

r = oDb.exec_query(drop_tbl_query)
r = oDb.exec_query(create_tbl_query)

# Create SEQUENCE

create_seq_query = """
DROP SEQUENCE IF EXISTS DB_SCHEMA.SEQUENCE_NAME CASCADE;
CREATE SEQUENCE DB_SCHEMA.SEQUENCE_NAME;
ALTER TABLE DB_SCHEMA.TABLE_NAME ALTER id SET DEFAULT NEXTVAL('DB_SCHEMA.SEQUENCE_NAME');
ALTER SEQUENCE DB_SCHEMA.SEQUENCE_NAME RESTART WITH 1;
""".replace('DB_SCHEMA', DB_SCHEMA)\
.replace('SEQUENCE_NAME', SEQUENCE_NAME)\
.replace('TABLE_NAME', TABLE_NAME)

r = oDb.exec_query(create_seq_query)