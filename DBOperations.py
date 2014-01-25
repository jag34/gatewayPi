import sqlite3
import unittest
import datetime
import os
__author__ = 'jag'
USAGE_DB='usage.db'
PORT_FWD_DB='portfwd.db'

class Route(object):

    def __init__(self, port, dst):
        self.port = port
        self.dst = dst

class DataUsage(object):

    def __init__(self, rx, tx):
        self.rx = rx
        self.tx = tx

class PortFwdingManager(object):

    def __init__(self, filename=PORT_FWD_DB):
        create_db = False
        if not os.path.exists(filename):
            os.mknod(filename)
            create_db = True

        self.db_conn = sqlite3.connect(filename)
        self.cursor = self.db_conn.cursor()
        self.table_name = 'routes'

        if create_db:
            self.cursor.execute('''CREATE TABLE {table} (port INT, dst varchar)'''.format(table=self.table_name))
            self.db_conn.commit()

    def inserToDB(self, rule):
        self.cursor.execute("INSERT INTO {table} VALUES ( {port} , '{destination}' );".format(table=self.table_name,
                                                                                              port=rule.port,
                                                                                              destination=rule.dst))
        self.db_conn.commit()

    def close(self):
        self.cursor.close()
        self.db_conn.close()

class UsageManager(object):
    def __init__(self, filename=USAGE_DB):
        create_db = False
        if not os.path.exists(filename):
            os.mknod(filename)
            create_db = True

        self.db_conn = sqlite3.connect(filename)
        self.cursor = self.db_conn.cursor()
        self.table_name = 'usage'

        if create_db:
            self.cursor.execute('''CREATE TABLE {table} (day Date, download INT, upload INT)'''.format(table=self.table_name))
            self.db_conn.commit()

    def insertToDB(self, datausage):
        now = datetime.datetime.now()
        self.cursor.execute("INSERT INTO {table} VALUES ( '{date}', {tx} , {rx} );".format(table=self.table_name,
                                                                                              date=now,
                                                                                              tx=datausage.rx,
                                                                                              rx=datausage.tx))
        self.db_conn.commit()

    def close(self):
        self.cursor.close()
        self.db_conn.close()

class DBUnitTest(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.usage_mgr = UsageManager()
        self.port_fwding_mgr = PortFwdingManager()

    def tearDown(self):
        self.usage_mgr.close()
        self.port_fwding_mgr.close()

    def test_createDb(self):
        os.remove(PORT_FWD_DB)
        os.remove(USAGE_DB)
        self.setUp()
        self.assertTrue(os.path.exists(PORT_FWD_DB))
        self.assertTrue(os.path.exists(USAGE_DB))

    def test_insert_usage(self):
        usage = DataUsage(8220, 12334)
        self.usage_mgr.insertToDB(usage)

    def test_insert_route(self):
        route = Route(80, '10.0.1.1')
        self.port_fwding_mgr.inserToDB(route)

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(DBUnitTest))
unittest.TextTestRunner(verbosity=3).run(suite)