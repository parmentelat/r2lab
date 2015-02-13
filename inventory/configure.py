#!/usr/bin/env python3

"""
Assumptions here:
(*) node with physical number 33 has its CM card burned with 
    MAC address 02:00:00:00:00:33 
(*) when eth0 has MAC address xx.xx.xx.xx.xx.81 then 
    eth1 has MAC address xx.xx.xx.xx.xx.80
    this is probably too strong an assumption 
    but is hopefully good enough for now
"""

import re
import csv
import json

from argparse import ArgumentParser

from collections import OrderedDict

########################################
mac_regexp = re.compile ('(?P<prefix>([0-9A-Fa-f]{2}:){5})(?P<last>[0-9A-Fa-f]{2})')

class Node(object):
    """
    a single node, defined with its physycal number (given once and for good)
    a logical number (the actual slot in the testbed where this node sits)
    and a mac addredd (the one attached to its physical eth device)
    ---
    """
    def __init__(self, phy_num, log_num, mac, alt_mac):
        self.phy_num = phy_num
        self.log_num = log_num
        self.mac = mac.lower()
        self.alt_mac = alt_mac.lower()

    def phy_str0(self):
        "physical number on 2 chars as a str"
        return "{:02d}".format(self.phy_num)
    def phy_name(self):
        "external name based on physical number, like phy33"
        return "phy"+self.phy_str0()

    def log_name(self, prefix='fit'):
        "external name based on logical number, like fit33"
        return "{prefix}{:02d}".format(self.log_num, prefix=prefix)

    subnets = ( (1, 'reboot'), (2, 'data'), (3, 'control') )

    def json_model(self):
        domain = 'faraday'
        return {
            "name": self.log_name(),
            "hostname": self.phy_name(),
            "hardware_type": "PC-Icarus",
            "urn": "urn:publicid:IDN+omf:faraday+node+"+self.log_name(),
            "interfaces": [
                {
                    "name": self.log_name()+":if0",
                    "role": "control",
                    "mac": self.mac,
                    "ip": {
                        # we cannot change the IP address of the CMC ...
                        "address": "192.168.3.{}".format(self.phy_num),
                        "netmask": "255.255.255.0",
                        "ip_type": "ipv4"
                    }
                },
                {
                    "name": self.log_name()+":if1",
                    "role": "experimental",
                    "mac": self.alt_mac
                }
            ],
            "cmc": {
                "name": self.log_name()+":cm",
                "mac": "02:00:00:00:00:"+self.phy_str0(),
                "ip": {
                    "address": "192.168.1.{}".format(self.log_num),
                    "netmask": "255.255.255.0",
                    "ip_type": "ipv4"
                }
            },
            "cpu": {
                "cpu_type": "Intel 4770kI7",
                "cores": 4,
                "threads": 8,
                "cache_l1": "n/a",
                "cache_l2": "8 Mb"
            },
            "ram": "8 GB",
            "ram_type": "DIMM Synchronous",
            "hd_capacity": "240 GB"
        }

    def dnsmasq_conf(self):
        control="dhcp-host=net:control,{},{},192.168.3.{}\n".\
            format(self.mac, self.log_name('fit'), self.log_num)
        data="dhcp-host=net:data,{},{}-exp,192.168.2.{}\n".\
            format(self.alt_mac, self.log_name('data-'), self.log_num)
#        return control+data
        return control


    def hosts_conf_sn(self, sn_ip, sn_name):
        # we cannot change the IP address of the CMC card, so this one is physical
        is_cmc = (sn_ip == self.subnets[0][0])
        num = self.phy_num if is_cmc else self.log_num
        hostnames = self.log_name(prefix=sn_name+'-')
        if sn_name == 'control':
            hostnames += " " + self.log_name()
        return "192.168.{sn_ip}.{num}\t{hostnames}\n".format(**locals())

    def hosts_conf(self):
        return "".join([self.hosts_conf_sn(i,n) for (i,n) in self.subnets])

    def nagios_host_cfg_sn(self, sn_ip, sn_name):
        log_name=self.log_name()
        sn_ip=sn_ip
        sn_name=sn_name
        # we cannot change the IP address of the CMC card, so this one is physical
        is_cmc = (sn_ip == self.subnets[0][0])
        num = self.phy_num if is_cmc else self.log_num

        ### NOTE: format uses { } already so for inserting a { or } we need to double them
        result = """define host {{
use fit-node
host_name {log_name}-{sn_name}
address 192.168.{sn_ip}.{num}
check_command my_ping
}}
""".format(**locals())

        if is_cmc:
            result += """ define service{{
use my-service
host_name {log_name}-{sn_name}
service_description  ON/OFF
check_command on_off
}}
""".format(**locals())

        return result

    def nagios_host_cfg(self):
        return "".join([self.nagios_host_cfg_sn(i,n) for (i,n) in self.subnets])

    def nagios_groups(self):
        "returns a 3-list with the hostnames for the 3 subnets"
        log_name=self.log_name()
        return [ "{log_name}-{sn_name}".format(log_name=log_name, sn_name=sn_name)
                 for i, sn_name in self.subnets ]
    
    def diana_db(self):
        ip = "138.96.119.{}".format(100+self.phy_num)
        hostname=self.phy_name()
        mac1=self.mac
        mac2=self.alt_mac
        return "{ip} h={hostname} {mac1} o=alt:{mac2}\n".format(**locals())

########################################
hosts_header="""# Do not edit this file directly
# it is generated by configure.py

127.0.0.1	localhost

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

192.168.1.100   faraday faraday1
192.168.2.100   faraday2
192.168.3.100   faraday3
192.168.3.101   switch-reboot
192.168.3.102   switch-data
192.168.3.103   switch-control

##########
"""

dnsmasq_header="""# Do not edit this file directly
# it is generated by configure.py

### the 3 switches
# CONFIRMED to be the main data switch
dhcp-host=f8:b1:56:33:50:ad,switch-data,192.168.3.102

# CONFIRMED control
dhcp-host=f8:b1:56:42:51:32,switch-control,192.168.3.103

# has to be reboot then
dhcp-host=d0:67:e5:d6:ae:fe,switch-reboot,192.168.3.101


##########
"""

class Nodes(OrderedDict):
    """
    a repository of known nodes, indexed by physical number
    """
    def __init__(self, csv_filename, out_basename, verbose):
        OrderedDict.__init__(self)
        self.csv_filename = csv_filename
        self.out_basename = out_basename
        self.verbose = verbose

    def load(self):
        with open(self.csv_filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for lineno, line in enumerate(reader):
                try:
                    phy_num = int (line[1])
                    log_num = int (line[3])
                    # discard nodes that are not on-site
                    if not log_num:
                        print ("Ignoring physical node {phy_num} - not deployed".format(phy_num))
                        continue
                    mac = line[5]
                    match = mac_regexp.match(mac)
                    if match:
                        prefix, last = match.group('prefix', 'last')
                        byte = int (last, base=16)
                        alt_last = hex(byte-1)[2:]
                        alt_mac = prefix+alt_last
                        self[phy_num] = Node(phy_num, log_num, mac, alt_mac)
                    else:
                        print (lineno,'non-mac',mac)
                except Exception as e:
                    print ('skipping line',lineno,line)
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
    
    def keep_just_one(self):
        for k in self.keys()[1:]:
            del self[k]
        self.out_basename += ".small"

    def write_json(self):
        out_filename = self.out_basename+".json"
        with open (out_filename, 'w') as jsonfile:
            json_models = [ node.json_model() for node in self.values() ]
            json.dump (json_models, jsonfile)
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))


    def write_dnsmasq(self):
        out_filename = self.out_basename+".dnsmasq"
        with open (out_filename, 'w') as dnsmasqfile:
            dnsmasqfile.write(dnsmasq_header)
            for node in self.values():
                dnsmasqfile.write(node.dnsmasq_conf())
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))

    def write_hosts(self):
        out_filename = self.out_basename+".hosts"
        with open (out_filename, 'w') as hostsfile:
            hostsfile.write(hosts_header)
            for node in self.values():
                hostsfile.write(node.hosts_conf())
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))
    

    def write_nagios(self):
        out_filename = self.out_basename+"-nagios-nodes.cfg"
        with open(out_filename, 'w') as nagiosfile:
            for node in self.values():
                nagiosfile.write(node.nagios_host_cfg())
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))

    def write_nagios_hostgroups(self):
        out_filename = self.out_basename+"-nagios-groups.cfg"
        nodes_groups = zip(*[ node.nagios_groups() for node in self.values() ])
        with open(out_filename, 'w') as nagiosfile:
            for (i, sn_name), list_names in zip(Node.subnets, nodes_groups):
                sn_members = ",".join(list_names)
                hostgroup = """
define hostgroup {{
hostgroup_name .{i}
alias {sn_name}
members {sn_members}
}}
""".format(**locals())
                nagiosfile.write(hostgroup)
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))


    def write_diana_db(self):
        out_filename = self.out_basename+"-diana.db"
        with open(out_filename, 'w') as nagiosfile:
            for node in self.values():
                nagiosfile.write(node.diana_db())
        print ("(Over)wrote {out_filename} from {self.csv_filename}".format(**locals()))
        
########################################        
def main():
    parser = ArgumentParser()
    parser.add_argument("-v", "--verbose", action='store_true', default=False)
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("-s", "--small", action='store_true', default=False,
                        help="force output of only one node")
    parser.add_argument("input", nargs='?', default='fit.csv')
    args = parser.parse_args()

    nodes = Nodes(args.input, args.output or args.input.replace(".csv",""), args.verbose)
    nodes.load()

    # this is a debugging trick so that we generate only one node,
    # given how loading the JSON file is slow
    if args.small:
        nodes.keep_just_one()

    nodes.write_json()
    nodes.write_dnsmasq()
    nodes.write_hosts()
    nodes.write_nagios()
    nodes.write_nagios_hostgroups()
    nodes.write_diana_db()

    return 0

if __name__ == '__main__':
    exit(main())
