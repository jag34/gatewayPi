import sqlite3
import time
import pygal
import unittest
import datetime
import os
__author__ = 'jag'
USAGE_DB='/etc/sqlite3/usage.db'
PORT_FWD_DB='/etc/sqlite3/portfwd.db'

class Rule(object):

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

    def _inserToDB(self, rule):
        ret = True
        try:
            self.cursor.execute("INSERT INTO {table} VALUES ( {port} , '{destination}' );".format(table=self.table_name,
                                                                                              port=rule.port,
                                                                                              destination=rule.dst))
            self.db_conn.commit()
        except:
            ret = False

        return ret

    def addRoute(self, port, dst):
        new_rule = Rule(port, dst)
        return self._inserToDB(new_rule)

    def close(self):
        self.cursor.close()
        self.db_conn.close()

class UsageManager(object):
    def __init__(self, filename=USAGE_DB):
        create_db = False
        if not os.path.exists(filename):
            os.mknod(filename)
            create_db = True
        sqlite3.register_adapter(datetime.datetime, UsageManager._adapt_datetime)
        self.db_conn = sqlite3.connect(filename)
        self.cursor = self.db_conn.cursor()
        self.table_name = 'usage'

        if create_db:
            self.cursor.execute('''CREATE TABLE {table} (day Date, download INT, upload INT)'''.format(table=self.table_name))
            self.db_conn.commit()

    def _insertToDB(self, datausage):
        ret = True
        now = time.time()
        try:
            self.cursor.execute("INSERT INTO {table} VALUES ( '{now}', {tx} , {rx} );".format(table=self.table_name,
                                                                                                   now=now,
                                                                                                   tx=datausage.tx,
                                                                                                   rx=datausage.rx))
            self.db_conn.commit()
        except:
            ret = False

        return ret

    def _adapt_datetime(ts):
        return time.mktime(ts.timetuple())

    def addUsage(self, rx, tx):
        new_usage = DataUsage(rx, tx)
        return self._insertToDB(new_usage)

    def close(self):
        self.cursor.close()
        self.db_conn.close()

    def draw_usage_chart(self):
        #chart = pygal.Line(style=pygal.LightStyle)
        now = datetime.datetime.now()
        self.cursor.execute("select * from {table} where day > strftime('%s','now','-7 day');".format(table=self.table_name))
        #self.cursor.execute("SELECT ?", (now,))

        query_res = self.cursor.fetchone()

        while query_res is not None:
            date = query_res[0]
            tx = query_res[1]
            rx = query_res[2]

            print date
            query_res = self.cursor.fetchone()

class DBUnitTest(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.usage_mgr = UsageManager(filename="usage.db")
        self.port_fwding_mgr = PortFwdingManager(filename="portfwd.db")

    def tearDown(self):
        self.usage_mgr.close()
        self.port_fwding_mgr.close()

    def test_acreateDb(self):
        os.remove("portfwd.db")
        os.remove("usage.db")
        self.setUp()
        self.assertTrue(os.path.exists("portfwd.db"))
        self.assertTrue(os.path.exists("usage.db"))

    def test_binsert_usage(self):
        self.assertTrue(self.usage_mgr.addUsage(8220, 12334))
        self.assertTrue(self.usage_mgr.addUsage(111, 23451))
        self.assertTrue(self.usage_mgr.addUsage(23511, 112312312334))
        self.assertTrue(self.usage_mgr.addUsage(82123420, 121231334))

    def test_cinsert_route(self):
        route = Rule(80, '10.0.1.1')
        self.port_fwding_mgr._inserToDB(route)

    def test_draw_chart(self):
        self.usage_mgr.draw_usage_chart()

suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(DBUnitTest))
unittest.TextTestRunner(verbosity=3).run(suite)