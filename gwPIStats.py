__author__ = 'jag'

import psutil
import socket
import fcntl
import struct
import unittest
import threading
from datetime import timedelta
from subprocess import Popen, PIPE

class FSUsage(object):
    def __init__(self, fs, size, used, avail, usage, mounted):
        self.fs = fs
        self.size = size
        self.used = used
        self.avail = avail
        self.usage = usage
        self.mounted = mounted

class RouterClient(object):

    def __init__(self, mac, ip, hostname, expired=False):
        self.mac = mac
        self.ip = ip
        self.hostname = hostname
        self.expired = expired
        self.up = False

class GwPiMonitor(object):

    def __init__(self):
        self.cpus = psutil.NUM_CPUS
        self.cpu_usage = {}
        self.dhcp_clients = []
        self.mem_usage = (0,0)
        self.up_time = '0'
        self.fs_usages = []
        self.ip = '0.0.0.0'

        for i in range(self.cpus):
            self.cpu_usage[i] = 0

    def _ping_client(self, client=None, target=None):
        # Pings a client, or a target
        # returns true if successful, if it's a client
        # it'll store it in its data structure
        # false otherwise
        if client is not None and target is not None:
            return
        else:
            ping_client = None
            if client is not None:
                ping_client = client.ip
            if target is not None:
                ping_client = target

        ping_args = ['ping','-c', '1', '-W', '1', ping_client]
        p = Popen(ping_args, stdout=PIPE, stderr=PIPE, shell=False )
        p.communicate()

        if client is None:
            return p.returncode == 0
        else:
            client.up = p.returncode == 0
            return

    def _parse_leases_file(self):
        # dumpleases command prints all the leases from udhcp in a
        # nice format
        # creates user objects from this, and adds it to a list.
        leases_arg = ['dumpleases']
        p = Popen(leases_arg, stdout=PIPE, stdin=PIPE)
        stdout, stderr = p.communicate()

        # Put leases in a list
        lease_lines = stdout.split('\n')
        # First line it's just the table head
        del lease_lines[0]
        del lease_lines[len(lease_lines)-1]
        print lease_lines
        #Now remove spaces, and each lease will be an iterable
        #list with paramters set as:
        # Mac Address,IP Address,Host Name, Expires in
        for lease in lease_lines:
            lease = lease.split(' ')
            lease = filter(lambda x: x!='', lease)


            mac = lease[0]
            ip_addr = lease[1]
            if len(lease) > 3:
                host_name = lease[2]
                expired = lease[3] == 'expired'
            else:
                # Turns out, this one can sometimes be empty, because udhcp feels like it.
                # so this field might end up being a date...
                host_name = 'unknown'
                expired = lease[2] == 'expired'

            if not expired:
                client = RouterClient(mac, ip_addr, host_name,expired)
                self.dhcp_clients.append(client)

    def get_net_status(self, ifname='eth0'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                                s.fileno(),
                                0x8915,  # SIOCGIFADDR
                                struct.pack('256s', ifname[:15]))[20:24])

    def get_connected_status(self):
        return self._ping_client(target='8.8.8.8')
    
    def get_wap_status(self):
        return self._ping_client(target='10.0.1.2')

    def get_cpu_usage(self):
        # gets cpu usage
        current_usage = psutil.cpu_percent(interval=1, percpu=True)
        for cpu in range(len(current_usage)):
            self.cpu_usage[cpu] = current_usage[cpu]

    def get_mem_usage(self):
        # gets memory usage
        total, available, percent, used, free, active, inactive, buffers, cached = psutil.virtual_memory()
        self.mem_percent_usage = percent
        self.mem_available = "%.2f" %  (float(available)/pow(1024,2))
        self.mem_used = "%.2f" % (float(used)/pow(1024,2))

    def get_up_time(self):
        # parses the contents of the uptime file
        # blame problems to http://planzero.org/blog/2012/01/26/system_uptime_in_python,_a_better_way
        f = open('/proc/uptime', 'r')
        uptime_seconds = float(f.readline().split()[0])
        self.up_time_str = str(timedelta( seconds=uptime_seconds ))[:-7]

    def connected_clients(self):
        # dumpleases helps determining clients currently up
        # we can easily ping them to verify if they're up...
        # automate an expse? because it's fun ;)
        self._parse_leases_file()
        clients = 0
        threadList = []
        for client in self.dhcp_clients:
            p = threading.Thread(target=self._ping_client, args=[client])
            threadList.append(p)
            p.start()

        for thread in threadList:
            thread.join()

        for client in self.dhcp_clients:
            if client.up:
                clients += 1

        return clients

    def get_filesystem_usage(self):
        # df -h output
        df_args = [ 'df', '-h' ]
        p = Popen(df_args, stdout=PIPE, stdin=PIPE)
        stdout, stderr = p.communicate()

        # Put leases in a list
        fs_lines = stdout.split('\n')

        # First line it's just the table head
        del fs_lines[0]
        del fs_lines[len(fs_lines)-1]

        #Now remove spaces, and each lease will be an iterable
        #list with paramters set as:
        # Mac Address,IP Address,Host Name, Expires in
        for fs_line in fs_lines:
            fs = fs_line.split(' ')
            fs = filter(lambda x: x!='', fs)

            fs_usage = FSUsage(fs[0], fs[1], fs[2], fs[3], fs[4], fs[5] )
            self.fs_usages.append(fs_usage)

class UnitTesTGwMonitor(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.monitor = GwPiMonitor()

    def test_CpuUsage(self):
        self.monitor.get_cpu_usage()
        cpu_usage = self.monitor.cpu_usage
        print cpu_usage
        self.assertTrue(cpu_usage is not None)

    def test_FileSystemUsage(self):
        self.monitor.get_filesystem_usage()
        file_systems = self.monitor.fs_usages
        print file_systems
        self.assertTrue(file_systems is not None)

    def test_MemUsage(self):
        self.monitor.get_mem_usage()
        mem_usage = self.monitor.mem_usage
        print mem_usage
        self.assertTrue(mem_usage is not None)

    def test_UpTime(self):
        self.monitor.get_up_time()
        up_time = self.monitor.up_time_str
        print up_time
        self.assertTrue(len(up_time))

    def test_NetStatus(self):
        ip = self.monitor.get_net_status()
        print ip
        self.assertTrue(len(ip))
        self.assertTrue(self.monitor.get_connected_status)
    
    def test_ClientsOnline(self):
        clients = self.monitor.connected_clients()
        print clients
        self.assertTrue(clients > 0 )

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnitTesTGwMonitor))
    unittest.TextTestRunner(verbosity=3).run(suite)
