#!/usr/bin/env python

# for using print() in python3-style even in python2
from __future__ import print_function

# import nepi library and other required packages
from nepi.execution.ec import ExperimentController
from nepi.execution.resource import ResourceAction, ResourceState
from nepi.util.sshfuncs import logger

# creating an ExperimentController (EC) to manage the experiment
# the exp_id name should be unique for your experiment
# it will be used on the various resources
# to store results and similar functions
ec = ExperimentController(exp_id="A1-ping")

# we want to run a command right in the r2lab gateway
# so we need to define ssh-related details for doing so
gateway_hostname  = 'faraday.inria.fr'
gateway_username  = 'onelab.inria.mario.tutorial'
gateway_key       = '~/.ssh/onelab.private'

# creating a node object using our credentials
# this object will host the commands need to be run on the gateway
node = ec.register_resource("linux::Node",
                            username = gateway_username,
                            hostname = gateway_hostname,
                            identity = gateway_key,
                            # recommended settings
                            cleanExperiment = True,
                            cleanProcesses = True)
ec.deploy(node)

# creating an application
app = ec.register_resource("linux::Application",
                           # the command to execute
                           command='ping -c1 google.fr')
ec.deploy(app)

# connect app to node
# this is what says that this command will be run on faraday
ec.register_connection(app, node)

# and finally waiting for the app to finish its job
ec.wait_finished(app)

# recovering the results
print ("--- INFO : experiment output:",
       ec.trace(app, "stdout"))

# shutting down the experiment
ec.shutdown()
