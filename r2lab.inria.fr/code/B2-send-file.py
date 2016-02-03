#!/usr/bin/env python

# including nepi library and other required packages
from __future__ import print_function
from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState
from nepi.util.sshfuncs import logger
import os

# setting up the default host, onelab user and shh key credential
host_gateway  = 'faraday.inria.fr'
user_gateway  = '[your_onelab_user]'
user_identity = '~/.ssh/[your_public_ssh_key]'
gateway_dir 	= '/home/[your_onelab_user]/'

# setting up the credentials for the nodes 
host01 = 'fit01'
user01 = 'root'
host01_dir = '/home/'

host02 = 'fit02'
user02 = 'root'
host02_dir = '/home/'
port   = 1234

local_file = '[some_file.txt]'
local_dir  = '[some_file_path]'

wifi_interface = 'wlan2' 
wifi_channel   = '4'
wifi_name      = 'ad-hoc'
wifi_key       = '1234567890'

wifi_net_mask  = '/24'
wifi_ip_fit01  = '172.16.1.1'
wifi_ip_fit02  = '172.16.1.2'

# creating a new ExperimentController (EC) to manage the experiment
ec = ExperimentController(exp_id="B2-send-file")

# creating local
local   = ec.register_resource("linux::Node",
                              hostname = localhost,
                              cleanExperiment = True,
                              cleanProcesses = True)

# creating the gateway node
gateway = ec.register_resource("linux::Node",
                             	username = user_gateway,
                             	hostname = host_gateway,
                             	identity = user_identity,
                              cleanExperiment = True,
                              cleanProcesses = True)

# creating the fit01 node
fit01 	= ec.register_resource("linux::Node",
                            	username = user01,
                            	hostname = host01,
                            	gateway = host_gateway,
                            	gatewayUser = user_gateway,
                            	identity = user_identity,
                            	cleanExperiment = True,
                            	cleanProcesses = True)

# creating the fit02 node 
fit02   = ec.register_resource("linux::Node",
                            	username = user02,
                            	hostname = host02,
                            	gateway = host_gateway,
                            	gatewayUser = user_gateway,
                            	identity = user_identity,
                            	cleanExperiment = True,
                            	cleanProcesses = True)

# application to setup data interface on fit01 node
app_adhoc_fit01 = ec.register_resource("linux::Application")
#cmd = 'sudo ip link set dev data down; sudo dhclient data;'
# configuring the ad-hoc for node fit01
cmd  = "ip addr flush dev {}; ".format(wifi_interface)
cmd += "sudo ip link set {} down; ".format(wifi_interface)
cmd += "sudo iwconfig {} mode ad-hoc; ".format(wifi_interface)
cmd += "sudo iwconfig {} channel {}; ".format(wifi_interface, wifi_channel)
cmd += "sudo iwconfig {} essid '{}'; ".format(wifi_interface, wifi_name)
cmd += "sudo iwconfig {} key {}; ".format(wifi_interface, wifi_key)
cmd += "sudo ip link set {} up; ".format(wifi_interface)
cmd += "sudo ip addr add {}{} dev {}; ".format(wifi_ip_fit01, wifi_net_mask, wifi_interface)
ec.set(app_adhoc_fit01, "command", cmd)
ec.register_connection(app_adhoc_fit01, fit01)

# application to setup data interface on fit02 node
app_adhoc_fit02 = ec.register_resource("linux::Application")
#cmd = 'sudo ip link set dev data down; sudo dhclient data;'
# configuring the ad-hoc for node fit01
cmd  = "ip addr flush dev {}; ".format(wifi_interface)
cmd += "sudo ip link set {} down; ".format(wifi_interface)
cmd += "sudo iwconfig {} mode ad-hoc; ".format(wifi_interface)
cmd += "sudo iwconfig {} channel {}; ".format(wifi_interface, wifi_channel)
cmd += "sudo iwconfig {} essid '{}'; ".format(wifi_interface, wifi_name)
cmd += "sudo iwconfig {} key {}; ".format(wifi_interface, wifi_key)
cmd += "sudo ip link set {} up; ".format(wifi_interface)
cmd += "sudo ip addr add {}{} dev {}; ".format(wifi_ip_fit02, wifi_net_mask, wifi_interface)
ec.set(app_adhoc_fit02, "command", cmd)
ec.register_connection(app_adhoc_fit02, fit02)

# application to copy file from local to gateway
app_local = ec.register_resource("linux::Application")
cmd  = 'scp {}{} {}@{}:{}{}; '.format(local_dir, local_file, user_gateway, host_gateway, gateway_dir, local_file)
ec.set(app_local, "command", cmd)
ec.register_connection(app_local, local)

# application to copy file to fit02 from gateway
app_gateway = ec.register_resource("linux::Application")
cmd  = 'scp {}{} {}@{}:{}{}; '.format(gateway_dir, local_file, user02, host02, host02_dir, local_file)
ec.set(app_gateway, "command", cmd)
ec.register_connection(app_gateway, gateway)

# fit01 will receive the file from fit02, then we start listening in the port
app_fit01 = ec.register_resource("linux::Application")
cmd = 'nc -dl {} > {}{}'.format(port, host01_dir, local_file)
ec.set(app_fit01, "depends", "netcat")
ec.set(app_fit01, "command", cmd)
ec.register_connection(app_fit01, fit01)

# fit02 will send the file to fit01 
app_fit02 = ec.register_resource("linux::Application")
cmd = 'nc {} {} < {}{}'.format(wifi_ip_fit01, port, host02_dir, local_file)
ec.set(app_fit02, "depends", "netcat")
ec.set(app_fit02, "command", cmd)
ec.register_connection(app_fit02, fit02)

# fit02 will list the dir after all process 
app_fit02_ls = ec.register_resource("linux::Application")
cmd = 'ls -la {}'.format(host02_dir)
ec.set(app_fit02_ls, "command", cmd)
ec.register_connection(app_fit02_ls, fit02)

# defining that the node gateway can copy the file to fit02 only after the file is copied to it from local
ec.register_condition(app_gateway, ResourceAction.START, app_local, ResourceState.STOPPED) 

# defining that the node ftt02 can send the file to fit01 only after the file is copied to it from gateway
ec.register_condition(app_fit02, ResourceAction.START, app_gateway, ResourceState.STOPPED) 

# defining that the node fit02 can send only after node fit01 is listening
ec.register_condition(app_fit02, ResourceAction.START, app_fit01, ResourceState.STARTED)

# defining that the node fit02 can send only after node fit01 is listening
ec.register_condition(app_fit02_ls, ResourceAction.START, app_fit02, ResourceState.STOPPED) 

# deploy all applications
ec.deploy([local, gateway, fit01, fit02, app_local, app_gateway, app_adhoc_fit01, app_fit01, app_adhoc_fit02, app_fit02, app_fit02_ls])

#wait ls application to recovery the results and present after
ec.wait_finished(app_fit02_ls)

# recovering the results
print ("\n--- INFO: listing directory on fit02:")
print (ec.trace(app_fit02_ls, "stdout"))

# shutting down the experiment
ec.shutdown()