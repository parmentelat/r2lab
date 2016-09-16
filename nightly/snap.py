#!/usr/bin/env python3
#
# Author file: Mario Zancanaro <mario.zancanaro@inria.fr>
#
"""
As convenience tool to save a snapshot of R2lab nodes and recover in a future moment
"""

import re
import os, os.path
import json
import subprocess
from subprocess import Popen
import time
import sys
import copy
from collections import OrderedDict
from argparse import ArgumentParser
from datetime import datetime
from sys import version_info
from collections import OrderedDict
import progressbar
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, Timer, AdaptiveETA



IMAGEDIR        = '/var/lib/rhubarbe-images/'
NODE_TAG_IMAGE  = '/etc/rhubarbe-image' #this is a TAG, not a folder
ADD_IN_NAME     = '_snap_'
ADD_IN_FOLDER   = '_snapshots'
DEFAULT_IMAGE   = 'fedora-23.ndz'

FILEDIR = "/root/r2lab/nightly/"
try:
    os.listdir(FILEDIR)
except Exception as e:
    #for my local dir
    FILEDIR = "/Users/nano/Documents/Inria/r2lab/nightly/"

USER_IMAGEDIR = '/var/lib/rhubarbe-images/'
try:
    os.listdir(USER_IMAGEDIR)
except Exception as e:
    #for my local dir
    USER_IMAGEDIR = '/Users/nano/'



def main():
    """
    """
    parser = ArgumentParser()
    parser.add_argument("-n", "--nodes", dest="nodes", default='all',
                        help="Comma separated list of nodes")
    parser.add_argument("-s", "--save", dest="save_snapshot",
                        help="Save r2lab snapshot based in the current image name")
    parser.add_argument("-p", dest="persist", action='store_true',
                        help="Persist the current image as a new one")
    parser.add_argument("-l", "--load", dest="load_snapshot",
                        help="Load a given snapshot")
    parser.add_argument("-v", "--view", dest="view_snapshot", default=None,
                        help="View a given snapshot")
    args = parser.parse_args()

    save_snapshot  = args.save_snapshot
    persist        = args.persist
    load_snapshot  = args.load_snapshot
    view_snapshot  = args.view_snapshot
    nodes          = args.nodes

    #save
    if save_snapshot is not None:
        save(format_nodes(nodes), save_snapshot, persist)
    #load
    elif load_snapshot is not None:
        load(load_snapshot)
    #view
    elif view_snapshot is not None:
        view(view_snapshot)
    else:
        view(view_snapshot)
    return 0



def save(nodes, snapshot, persist=False):
    """ save a snapshot for the user according nodes state using threading
    """
    file    = snapshot+'.snap'
    path    = os.getcwd()+'/'+file
    db      = {}
    errors  = []

    print('INFO: saving snapshot...')
    on_nodes, off_nodes = split_nodes_by_status(nodes)
    print('INFO: checking node images...')
    for node in off_nodes:
        db.update( {str(node) : {"state":'off', "imagename":DEFAULT_IMAGE}})

    widgets = ['INFO: ', Percentage(), ' | ', Bar(), ' | ', Timer()]
    i = 0
    for node in on_nodes:
        if i == 0: bar = progressbar.ProgressBar(widgets=widgets,maxval=len(nodes)).start()
        db.update( {str(node) : {"state":'on' , "imagename":fetch_last_image(node)}})
        i = i + 1
        time.sleep(0.1)
        bar.update(i)
    if i > 0: print('\r')
    if persist and on_nodes: persist_image(on_nodes, snapshot, db, errors)

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception as e:
        print('ERROR: something went wrong in create directory in home.')
        exit(1)
    with open(path, "w+") as f:
        f.write(json.dumps(db)+"\n")
    if errors:
        print('INFO: something went wrong in the process of save your snapshot. Check it out:')
        for error in errors:
            print(error)
    else:
        print('INFO: snapshot saved. Enjoy!')



def load(user, snapshot):
    """ load an already saved snapshot for the user
    """



def view(snapshot):
    """ run the load command grouped by images and nodes
    """
    if snapshot is None:
        print("ERROR: snapshot name was not informed.")
        exit(1)



def split_nodes_by_status(nodes):
    """ split nodes in a list of on/off state nodes
    """
    print('INFO: checking node status...')
    widgets = ['INFO: ', Percentage(), ' | ', Bar(), ' | ', Timer()]
    bar = progressbar.ProgressBar(widgets=widgets,maxval=len(nodes)).start()
    on_nodes  = []
    off_nodes = []
    i = 0
    for node in nodes:
        node_status = check_status(node, 1)
        if 'on' in node_status:
            on_nodes.append(node)
        else:
            off_nodes.append(node)
        i = i + 1
        time.sleep(0.1)
        bar.update(i)
    print('\r')
    return (on_nodes, off_nodes)



def persist_image(on_nodes, snapshot, db, errors):
    """ save the images using rhubarbe
    """
    widgets = ['INFO: ', Percentage(), ' | ', Bar(), ' | ', Timer()]
    create_user_folder()
    clean_old_files()

    answers = persist_image_with_rhubarbe(on_nodes, snapshot)
    if True in answers:
        errors.append('ERROR: one or more image node could not be saved.')
    print('INFO: arranging files...')
    i = 0
    bar = progressbar.ProgressBar(widgets=widgets,maxval=len(on_nodes)).start()

    #move each saved file to the user snapshots folder
    for node in on_nodes:
        #searching for saved file give by rsave
        saved_file = fetch_saved_file_by_rhubarbe(node)
        file_path, file_name = os.path.split(str(saved_file))
        db.update( {str(node) : { "state" : 'on', "imagename" : file_name } } )
        if saved_file:
            user_folder = my_user_folder()
            os.rename(saved_file, user_folder+file_name)
        else:
            errors.append('ERROR: could not find file for node fit{}.'.format(node))
        i = i + 1
        time.sleep(0.1)
        bar.update(i)
    print('\r')



def persist_image_with_rhubarbe(nodes, snapshot):
    """ forks the rhubarbe save command
    """
    print('INFO: saving images. This may take a little while.')
    file_part   = code()+ADD_IN_NAME
    jobs_ans    = []
    i           = 0
    jobs        = [Popen("rhubarbe save {} -o {}".format(node, file_part),
                        shell=True, stdout=subprocess.PIPE)
                        for node in nodes]
    for job in jobs:
        jobs_ans.append(job.wait())
    return jobs_ans



def check_status(node, silent=0):
    """ return the state of each node. On and Off are searched.
    """
    options = ['on', 'already on', 'off', 'already off']
    command = 'curl -s reboot{}/status;'.format(node)
    ans_cmd = run(command)

    if not ans_cmd['status'] or ans_cmd['output'] not in options:
        if silent is 0:
            print('WARNING: could not detect the status of node #{}. It will be set as "off".'.format(node))
        return "off"
    else:
        return ans_cmd['output']



def create_user_folder():
    """ create a user folder in images folder
    """
    user = fetch_user()
    folder = user + ADD_IN_FOLDER
    path = USER_IMAGEDIR + folder + '/'

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception as e:
        print('ERROR: something went wrong in create directory in images folder.')
        exit(1)



def my_user_folder():
    """ create a user folder in images folder
    """
    user = fetch_user()
    folder = user + ADD_IN_FOLDER
    path = USER_IMAGEDIR + folder +'/'
    if os.path.exists(path):
        return path
    else:
        print('ERROR: something went wrong in read user directory images folder.')
        exit(1)



def fetch_last_image(node):
    """ recover the last image save in the node
    """
    image_name = DEFAULT_IMAGE
    if os.path.exists(NODE_TAG_IMAGE):
        try:
            command = "ssh root@fit{} cat {} | tail -n1 | awk '{{print $7}}'".format(node, NODE_TAG_IMAGE)
            ans_cmd = run(command)
            if ans_cmd['status']:
                ans = ans_cmd['output'].lower()
                if not 'no such file' or not 'could not resolve' in ans:
                    image_name = ans
        except Exception as e:
            pass
            # print('WARNING: image was not found. The default {} will be set.'.format(image_name))
    return image_name



def code():
    """ give me a small hash code from user name
    """
    user = fetch_user()
    return str(abs(hash(user)) % (10 ** 8))



def clean_old_files():
    """ move the old files with signature of user code + _snap_ to its folder
    """
    user_folder = my_user_folder()
    file_part_name = code()+ADD_IN_NAME
    command = "mv {}*saving__*{}.ndz {}".format(USER_IMAGEDIR, file_part_name, user_folder)
    ans_cmd = run(command)



def fetch_saved_file_by_rhubarbe(node):
    """ list the images dir in last modified file order
    """
    file_part_name = code()+ADD_IN_NAME
    command = "ls -la {}*saving__fit{}_*{}.ndz | awk '{{print $9}}'".format(USER_IMAGEDIR, node, file_part_name)
    ans_cmd = run(command)
    if ans_cmd['status']:
        ans = ans_cmd['output']
        if 'No such file or directory' in ans:
            return False
        else:
            return ans
    else:
        return False



def wait_and_update_progress_bar(wait_for):
    """ print the progress bar when waiting for a while
    """
    for n in range(wait_for):
        time.sleep(1)
        print('.', end=''),
        sys.stdout.flush()
    print("")



def command_in_curl(nodes, action='status'):
    """ transform the command to execute in CURL format
    """
    in_curl = map(lambda x:'curl reboot'+str('0'+str(x) if x<10 else x)+'/'+action, nodes)
    in_curl = '; '.join(in_curl)
    return in_curl



def fetch_user():
    """ identify the logged user
    """
    command = 'whoami'
    ans_cmd = run(command)
    if ans_cmd['status']:
        return ans_cmd['output']
    else:
        print('ERROR: user not detected.')
        exit(1)



def run(command):
    """ run the commands
    """
    p   = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = p.communicate()
    ret        = p.wait()
    out        = out.strip().decode('ascii')
    err        = err
    ret        = True if ret == 0 else False
    return dict({'output': out, 'error': err, 'status': ret})



def parse_results_from_load(text):
    """ return a list of successfully load nodes found in the log/answer
    """
    text    = text.lower()
    search  = "uploading successful"
    idxs    = [n for n in range(len(text)) if text.find(search, n) == n]
    back_in = 7 #fit02 is 5 + two spaces use it on split
    split_by= ' '
    found   = []
    for idx in idxs:
        found.append(text[idx-back_in : idx].split(split_by)[1])
    found = map(lambda each:each.strip("fit"), found)
    found = list(set(found))
    return found



def all_nodes():
    """ return the list of all nodes
    """
    nodes = range(1,38)
    nodes = list(map(str, nodes))
    for k, v in enumerate(nodes):
        if int(v) < 10:
            nodes[k] = v.rjust(2, '0')

    return nodes



def new_list_nodes(nodes):
    """ put nodes in string list format with zero left
    """
    if not type(nodes) is list:
        if ',' in nodes:
            nodes = nodes.split(',')
        elif '-' in nodes:
            nodes = nodes.strip("[]").split('-')
            nodes = range(int(nodes[0]), int(nodes[1])+1)
        else:
            nodes = [nodes]

    new_list_nodes = list(map(str, nodes))
    for k, v in enumerate(new_list_nodes):
        if int(v) < 10:
            new_list_nodes[k] = v.rjust(2, '0')

    return new_list_nodes



def format_nodes(nodes, avoid=None):
    """ correct format when inserted 'all' in -i / -r nodes parameter
    """
    to_remove = avoid

    if 'all' in nodes:
        nodes = all_nodes()
    else:
        nodes = new_list_nodes(nodes)

    if to_remove:
        to_remove = new_list_nodes(to_remove)
        nodes = [item for item in nodes if item not in to_remove]

    return nodes



def ask(message):
    """ interruption for an user input
    """
    py3 = version_info[0] > 2
    if py3:
        response = input(message)
    else:
        response = raw_input(message)
    return response



if __name__ == '__main__':
    exit(main())
