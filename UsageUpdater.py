#! /usr/bin/python -u

__author__ = 'jag'
from DBOperations import UsageManager
from subprocess import Popen, PIPE
import sys

def strToInt(usage):
    if (usage[-1:] == 'K'):
        usage=int(usage[:-1])*1024
    elif (usage[-1:] == 'M'):
        usage=int(usage[:-1])*(pow(1024,2))
    elif (usage[-1:] == 'G'):
        usage=int(usage[:-1])*(pow(1024,3))
    else:
        usage = None

    return usage

iptables_rx_cmd = ['iptables','-nvL','FW-OPEN']
iptables_tx_cmd = ['iptables','-nvL','FW-INTERFACES']
iptables_counts_reset_cmd = ['iptables','-Z']

p_rx = Popen(iptables_rx_cmd, stdout=PIPE)
p_tx = Popen(iptables_tx_cmd, stdout=PIPE)

rx_cmd_out = p_rx.communicate()[0]
tx_cmd_out = p_tx.communicate()[0]

rx_line = rx_cmd_out.split('\n')[3]
rx_val = rx_line.split(' ')
rx_val = filter(lambda x: x!='', rx_val)[1]

ret = strToInt(rx_val)
if ret is not None:
    rx_val = ret
else:
    rx_val = 0

tx_line = tx_cmd_out.split('\n')[2]
tx_val = tx_line.split(' ')
tx_val = filter(lambda x: x!='', tx_val)[1]

ret = strToInt(tx_val)
if ret is not None:
    tx_val = ret
else:
    tx_val = 0

usage_mgr = UsageManager()
if usage_mgr.addUsage(rx_val,tx_val):
    p_z = Popen(iptables_counts_reset_cmd, stdout=PIPE, stderr=PIPE)
    p_z.communicate()
    sys.exit(0)
else:
    sys.exit(1)