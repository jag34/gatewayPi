import sqlite3
import time
import pygal
import unittest
import datetime
import os
import calendar
__author__ = 'jag'
USAGE_DB='/etc/sqlite3/usage.db'
PORT_FWD_DB='/etc/sqlite3/portfwd.db'

class Rule(object):

    def __init__(self, port, dst):
        self.port = port
        self.dst = dst

class DataUsage(object):

    def __init__(self, rx, tx, date=None):
        self.date = date
        self.rx = rx
        self.tx = tx

    def __eq__(self, other):
        return self.date == other.date

    def __str__(self):
        return str(self.date)+" "+str(self.rx)+","+str(self.tx)

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

        self.db_conn = sqlite3.connect(filename)
        self.cursor = self.db_conn.cursor()
        self.table_name = 'usage'
        self.records = []

        if create_db:
            self.cursor.execute('''CREATE TABLE {table} (day Date, download INT, upload INT)'''.format(table=self.table_name))
            self.db_conn.commit()

    def _insertToDB(self, datausage, time):
        ret = True
        now = time
        try:
            self.cursor.execute("INSERT INTO {table} VALUES ( '{now}', {rx} , {tx} );".format(table=self.table_name,
                                                                                                   now=now,
                                                                                                   tx=datausage.rx,
                                                                                                   rx=datausage.tx))
            self.db_conn.commit()
        except:
            ret = False

        return ret

    def addUsage(self, rx, tx, time=time.time()):
        new_usage = DataUsage(rx, tx)
        return self._insertToDB(new_usage, time)

    def close(self):
        self.cursor.close()
        self.db_conn.close()

    def draw_usage_chart(self):
        chart = pygal.Line(style=pygal.style.LightStyle)
        chart.title = "Data Usage in MB"
        self.cursor.execute("select * from {table} where day > strftime('%s','now','-7 day');".format(table=self.table_name))

        query_res = self.cursor.fetchone()
        while query_res is not None:
            date = query_res[0]
            tx = query_res[1]
            rx = query_res[2]

            print date
            record_date = datetime.datetime.fromtimestamp(date)
            print record_date
            record = DataUsage(rx, tx, record_date)
            self.records.append(record)
            query_res = self.cursor.fetchone()

        rx = []
        tx = []
        day = 0
        graph_record = None
        if len(self.records) < 25:
            # make a list for a single day records
            range_start = self.records[0].date.hour
            range_end = self.records[-1].date.hour
            chart.x_labels = map(str, range(range_start, range_end+1))
            for record in self.records:
                rx.append(record.rx/pow(2,12))
                tx.append(record.tx/pow(2,12))

        else:
            range_start = self.records[0].date.day
            range_end = self.records[-1].date.day
            chart.x_labels = map(str, range(range_start, range_end+1))
            for record in self.records:
                if day == 0:
                    # First record
                    graph_record = record
                elif day == record.date.day:
                    # Records within the same day.
                    graph_record.rx += record.rx
                    graph_record.tx += record.tx
                elif day != record.date.day:
                    # New record with a different day.
                    rx.append(graph_record.rx/pow(2,12))
                    tx.append(graph_record.tx/pow(2,12))

                    graph_record = record
                    day += 1

                # Insert the updated record in case it's
                # the last one in the list.
                if record == self.records[len(self.records)-1]:
                    rx.append(graph_record.rx/pow(2,12))
                    tx.append(graph_record.tx/pow(2,12))

        chart.add('Rx', rx)
        chart.add('Tx', tx)
        chart.render_to_file('line_chart.svg')

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
        self.assertTrue(self.usage_mgr.addUsage(7263232, 643072, calendar.timegm(datetime.datetime(2014,01,31,12).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(3056640, 360448,calendar.timegm(datetime.datetime(2014,01,31,13).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(434110464, 9245696, calendar.timegm(datetime.datetime(2014,01,31,14).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(1634729984, 23068672, calendar.timegm(datetime.datetime(2014,01,31,15).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(1378877440, 25165824, calendar.timegm(datetime.datetime(2014,01,31,16).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(524288000, 12582912, calendar.timegm(datetime.datetime(2014,01,31,17).timetuple())+(5*60*60)))
        self.assertTrue(self.usage_mgr.addUsage(465567744, 12582912, calendar.timegm(datetime.datetime(2014,01,31,18).timetuple())+(5*60*60)))

    def test_cinsert_route(self):
        route = Rule(80, '10.0.1.1')
        self.port_fwding_mgr._inserToDB(route)

    def test_draw_chart(self):
        self.usage_mgr.draw_usage_chart()

#suite = unittest.TestSuite()
#suite.addTest(unittest.makeSuite(DBUnitTest))
#unittest.TextTestRunner(verbosity=3).run(suite)