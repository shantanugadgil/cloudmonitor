#!/usr/bin/env python
# -*- coding: utf-8 -*-

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import subprocess
import json
import time
import argparse
import datetime
import pprint
import json, time, sys
import subprocess
import os
import jinja2
import traceback
import click

from jinja2 import FileSystemLoader
from jinja2 import Template
from jinja2 import BaseLoader,Environment,StrictUndefined,DebugUndefined,Undefined
from jinja2 import StrictUndefined

import datetime
import dateutil
from dateutil.parser import *
from pytz import timezone
import html

###############################################################################

script_dir = os.path.dirname(os.path.realpath(__file__))
template_dir = os.path.join(script_dir, 'templates')
config_dir = os.path.join('/etc', 'cloudmonitor')

###############################################################################

def _log(msg_str, color='green', onemore=0, blink=False):
    stack = traceback.extract_stack()

    # self is '-1'
    (filename1, line1, procname1, text1) = stack[-1]

    # caller is '-2'
    (filename2, line2, procname2, text2) = stack[-2]

    if onemore:
        (filename2, line2, procname2, text2) = stack[-3]

    curdate = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    click.secho('[{}] [{}] {}'.format(curdate, procname2, msg_str), fg=color, blink=blink)

###############################################################################

def log_fatal(msg_str):
    _log(msg_str, color='red', onemore=1, blink=True)
    sys.exit(1)

###############################################################################

def log_error(msg_str):
    _log(msg_str, color='red', onemore=1)

###############################################################################

def log_warn(msg_str):
    _log(msg_str, color='yellow', onemore=1)

###############################################################################

def log_info(msg_str):
    _log(msg_str, color='cyan', onemore=1)

###############################################################################

def log_debug(msg_str):
    _log(msg_str, color='white', onemore=1)

###############################################################################
def exec_local_cmd (_cmd):
    _log_info("[" + _cmd + "]")
    retcode = 0
    output = ''

    try:
        output = subprocess.check_output(_cmd, stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError as e:
        retcode = e.returncode
        output = e.output
        pass

    return retcode, output

###############################################################################

def render_template(info, template_file, target_file = None):
    template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), undefined=StrictUndefined)
    tm = template_env.get_template(template_file)
    msg = tm.render(info, info=info)

    try:
        if target_file:
            with open(target_file, 'w') as fp:
                fp.write(msg)

            log_info("template rendered successfully to file [%s]" % (target_file))
        else:
            return msg

    except Exception as e:
        traceback.print_exc()
        #log_error(repr(e))
        log_error(str(e))
        log_fatal("failed to render the template [%s] to [%s]" % (template_file, target_file))

###############################################################################

def add_to_context(context, region_dir, account, region):

    instance_file = os.path.join(region_dir, 'instances.json')
    image_file = os.path.join(region_dir, 'images.json')

    data_instances = {}
    log_debug("reading instance data from [" + instance_file + "]")
    try:
        with open(instance_file) as json_data:
            data_instances = json.load(json_data)
    except:
        log_error("unable to read instance data from file [" + instance_file + "]")
        return


    data_images = {}
    log_debug("reading image data from [" + image_file + "]")
    try:
        with open(image_file) as json_data:
            data_images = json.load(json_data)
    except:
        log_error("unable to read image data from file [" + image_file + "]")
        return


    # create a map of ami-id -> ami-name
    image_names = {}
    for i in data_images['Images']:
        image_names[ i['ImageId'] ] = i['Name']

    #pprint.pprint(image_names)

    items = []
    reservations = data_instances['Reservations']

    for r in reservations:
        instances = r['Instances']

        for instance in instances:

            status = instance['State']['Name']

            vpcid = '---'
            if 'VpcId' in instance:
                vpcid = instance['VpcId']

            private_ip_address = '-----'
            if 'PrivateIpAddress' in instance:
                private_ip_address = instance['PrivateIpAddress']

            public_ip_address = '-----'
            if 'PublicIpAddress' in instance:
                public_ip_address = instance['PublicIpAddress']

            key_name = '-----'
            if 'KeyName' in instance:
                key_name = instance['KeyName']

            tags = []
            if 'Tags' in instance:
                tags = instance['Tags']

            block_devices = []
            for dd in instance['BlockDeviceMappings']:
                block_devices.append(dd['DeviceName'])

            item = {}
            item['InstanceId']       = instance['InstanceId']
            item['Name']             = '---'
            item['BlockDevices']     = ' '.join(block_devices)
            item['Region']           = region
            item['Status']           = status

            item['KeyName']          = key_name
            item['InstanceType']     = instance['InstanceType']
            item['ImageId']          = instance['ImageId']

            # make the 'ImageName' default to the 'ImageId'
            # this is incase the image is not "owned" by "self"
            item['ImageName']        = instance['ImageId']
            
            if instance['ImageId'] in image_names:
                item['ImageName'] = image_names[ instance['ImageId'] ]

            #pprint.pprint(item['ImageName'])            

            item['PrivateIpAddress'] = private_ip_address
            item['VpcId']            = vpcid
            item['PublicIpAddress']  = public_ip_address

            str_utc = dateutil.parser.parse(instance['LaunchTime'])
            str_ist = str_utc.astimezone(timezone('Asia/Kolkata'))

            item['LaunchTime']       = str_ist

            # iterate over the tags to get some more data
            for tag in tags:
                if tag['Key'] in ['Name']:
                    item['Name'] = tag['Value']

            items.append(item)

    # FIXME: check if just an append can be used, since items is being initialized on top
    if 'items' in context[account]:
        context[account]['items'].extend(items)
    else:
        context[account]['items'] = items

###############################################################################
def main(args):
    context = {}

    context['accounts'] = []

    context['headers'] = ['InstanceId', 'Name', 'BlockDevices', 'Region', 'Status', 'KeyName', 'InstanceType', 'ImageId', 'ImageName', 'LaunchTime', 'PrivateIpAddress', 'VpcId', 'PublicIpAddress']
    context['footers'] = ['InstanceId', 'Name', 'BlockDevices', 'Region', 'Status', 'KeyName', 'InstanceType', 'ImageId', 'ImageName', 'LaunchTime', 'PrivateIpAddress', 'VpcId', 'PublicIpAddress']

    #pprint.pprint(args.data_dir)
    curdate = os.path.basename(args.data_dir)
    #pprint.pprint(curdate)
    context['curdate'] = curdate

    for account in os.listdir(args.data_dir):
        account_dir = os.path.join(args.data_dir, account)

        if not os.path.isdir(account_dir):
            continue

        # top-level list of accounts
        context['accounts'].append(account)

        # individual map of each account
        context[account] = {}
        context[account]['items'] = []

        for region in os.listdir(account_dir):
            region_dir = os.path.join(account_dir, region)

            if not os.path.isdir(region_dir):
                continue

            add_to_context(context, region_dir, account, region)

    #pprint.pprint(context)
    render_template(context, 'index.html.jinja', args.outfile)
    log_info("Done")
    sys.exit(0)

###############################################################################
### script begins here ###
###############################################################################

parser = argparse.ArgumentParser(prog='htmlgen', description='HTML Generator')

parser.add_argument('--config', action="store", help="Configuration file (not implemented yet)")
parser.add_argument('--data-dir', action="store", help="Data directory containing json files in tree structure", required=True)
parser.add_argument('--outfile', action="store", help="Output file", required=True)
args = parser.parse_args()

'''
#2021-04-12-14-21-21/
# ├── production
# │   ├── eu-central-1
# │   │   ├── images.json
# │   │   └── instances.json
# │   └── us-west-2
# │       ├── images.json
# │       └── instances.json
# └── staging
#     ├── eu-central-1
#     │   ├── images.json
#     │   └── instances.json
#     └── us-west-2
#         ├── images.json
#         └── instances.json
'''

#pprint.pprint(args)

main(args)

