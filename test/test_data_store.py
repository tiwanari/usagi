import os
import ast
import csv
from installer.tool_config import *

TESTDIR = os.path.dirname(os.path.abspath(__file__))
SIMPLE = TESTDIR + "/simple/search.ini"
PSQL_MYSQL = TESTDIR + "/psql_mysql/search.ini"

def test_pg_copy_raw_meta_data():
    silentremove("/tmp/simple.meta")

    sc = SearchConfiguration(SIMPLE)
    sc.get_search_config()
    parsed = sc.parse()

    assert parsed

    pg_handle = sc.handles[0]

    pg_handle.connect()
    pg_handle.copy_raw_meta_data("/tmp/simple.meta")
    pg_handle.close()

    with open("/tmp/simple.meta") as metadata:
        reader = csv.reader(metadata)
        n_tables = 0
        products_table_exists = 0
        for row in reader:
            n_tables += 1
            if row[0] == 'Products':
                products_table_exists += 1
                assert "xmin" in row[1]
                assert "productDescription" in row[1]
        assert n_tables == 8
        assert products_table_exists == 1


def test_pg_my_copy_raw_meta_data():
    silentremove("/tmp/psql_mysql.meta")

    sc = SearchConfiguration(PSQL_MYSQL)
    sc.get_search_config()
    parsed = sc.parse()

    assert parsed

    pg_handle = sc.handles[0]

    pg_handle.connect()
    pg_handle.copy_raw_meta_data("/tmp/psql_mysql.meta", append=True)
    pg_handle.close()

    my_handle = sc.handles[1]

    my_handle.connect()
    my_handle.copy_raw_meta_data("/tmp/psql_mysql.meta", append=True)
    my_handle.close()

    with open("/tmp/psql_mysql.meta") as metadata:
        reader = csv.reader(metadata)
        n_tables = 0
        products_table_exists = 0
        tennis_service_table_exists = 0
        for row in reader:
            n_tables += 1
            if row[0] == 'Products':
                products_table_exists += 1
                assert "xmin" in row[1]
                assert "productDescription" in row[1]
            if row[0] == 'sportsdb.tennis_service_stats':
                tennis_service_table_exists = 1
                assert "second_service_points_won" in row[1]
                assert "break_points_played" in row[1]
        assert n_tables == 144
        assert products_table_exists == 1
        assert tennis_service_table_exists == 1


import errno

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred
