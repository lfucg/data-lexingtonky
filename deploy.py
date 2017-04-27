#!/usr/bin/env python

"""
Deploy script for Amazon OpsWorks stacks

This script makes deploying "Dream" projects easy, but it makes some assumptions:

1. Your project structure should look as follows:
    $ tree -L 1 .
    .
    |-- README.md
    |-- chef-<cookbook_name>
    |-- deploy.py
    `- <app_dir>
2. If you intend to make use of this scripts' automated deployment of cookbook
   submodules, you'll need to configure your OpsWorks stack to use a custom
   cookbook source from S3.  The filename should start with chef-<cookbook_name>
   as it does above.  It is suggested to append the branch name in the filename
   (eg chef-<cookbook_name>-dev.zip)

Author:  Chris Allen
Created: 11/18/2016
"""

import argparse
import boto3
import glob
import os
import subprocess
import threading
import sys

from botocore.exceptions import ClientError
from datetime import datetime
from sys import exit
from time import sleep

# Parse args
parser = argparse.ArgumentParser(
    description='This program makes deploying to OpsWorks stupid proof!'
)
parser.add_argument(
    '--stack-ids',
    dest='stack_ids',
    help='OpsWorks stack IDs to deploy to',
    required=True
)

args = parser.parse_args()
STACK_IDS = args.stack_ids.split(',')

# Grab boto clients / restources
try:
    opsworks = boto3.client('opsworks')
    s3 = boto3.resource('s3')
except:
    print(
        "Your aws credentials are either not there or busted.  For more "
        "information visit: \nhttp://docs.aws.amazon.com/cli/latest/userguide/"
        "cli-chap-getting-started.html#config-settings-and-precedence\n"
    )
    exit(1)

def analyze_stack(stack, output=True):
    """
    Helper method that displays important information about a stack and
    parses out the useful stuff.

    Args:
        stack (dict): A dictionary describing an OpsWorks stack
        output (bool): A flag for printing

    Returns:
        apps (array): The apps that belong to the stack
        cookbook (dict): Pertinent information about the stack's cookbook
    """

    cookbookName = None
    cookbook = None
    apps = None
    try:
        if output: print("Stack: "+stack['Name'])
        if 'CustomCookbooksSource' in stack:
            cookbookDes = stack['CustomCookbooksSource'].get('Url')
            if cookbookDes is not None and 's3.amazonaws' in cookbookDes:
                cookbookPath = cookbookDes[25:]
                firstSlash = cookbookPath.find('/')
                cookbook = {
                    'bucket': cookbookPath[:firstSlash],
                    'cookbook_key': cookbookPath[firstSlash+1:],
                    'sha_key': cookbookPath[firstSlash+1:].replace('.zip', '_SHA.txt')
                }
                cookbookDirs = glob.glob('chef-*')
                if len(cookbookDirs) > 0:
                    if cookbookDirs[0] in cookbook['cookbook_key']:
                        cookbookName = cookbookDirs[0]
                        cookbook['local_sha'] = os.popen(
                            'cd '+cookbookDirs[0]+' && '+
                            'git log -n 1 --pretty=format:"%H"'
                        ).read()
                        cookbook['name'] = cookbookDirs[0]
                        try:
                            obj = s3.Object(
                                cookbook['bucket'],
                                cookbook['sha_key']
                            )
                            remote_sha = obj.get()["Body"].read().decode('utf-8')
                            cookbook['remote_sha'] = remote_sha
                        except:
                            cookbook['remote_sha'] = ''

                if output: print("--- Cookbook: "+cookbookName)
        r = opsworks.describe_apps(StackId=stack['StackId'])
        apps = r['Apps']
        if len(apps) == 0:
            if output: print("--- Apps: No apps")
        else:
            if output: print("--- Apps: "+str([app["Name"] for app in apps]))
    except ClientError as e:
        print(e)
    return apps, cookbook

def build_and_deploy_cookbook(cookbook):
    print('...Building cookbook ['+cookbook['name']+']')
    localCookbook = None
    try:
        cookbookDir = os.path.dirname(os.path.realpath(__file__)) + \
            '/'+cookbook['name']
        print('Gathering cookbook together into: ' + cookbookDir)
        FNULL = open(os.devnull, 'w')
        # Grab all the dependencies and put them in berks-cookbooks
        subprocess.check_call(['berks', 'vendor', '-q'],
            stdout=sys.stdout,  # XXX for debugging
            stderr=subprocess.STDOUT,
            cwd=cookbookDir
        )
        # Copy berksfile template
        subprocess.check_call(['cp', 'Berksfile.template', 'berks-cookbooks/Berksfile'],
            stdout=FNULL,
            stderr=subprocess.STDOUT,
            cwd=cookbookDir
        )
        # Zip it all up
        localCookbook = cookbook['name']+'.zip'
        subprocess.check_call(['zip', '-r', localCookbook, 'berks-cookbooks'],
            stdout=FNULL,
            stderr=subprocess.STDOUT,
            cwd=cookbookDir
        )

        print('...Deploying cookbook ['+cookbook['name']+']')
        # Upload zip of cookbook
        remoteCookbook = s3.Object(
            cookbook['bucket'],
            cookbook['cookbook_key']
        )
        response = remoteCookbook.put(
            ACL='private',
            Body=open(cookbook['name']+'/'+localCookbook, 'rb')
        )
        # Mark the new cookbook sha as deployed
        remoteSha = s3.Object(
            cookbook['bucket'],
            cookbook['sha_key']
        )
        response = remoteSha.put(ACL='private', Body=cookbook['local_sha'])
        # Clean up
        subprocess.call(['rm', '-rf', 'berks-cookbooks'],
            stdout=FNULL,
            stderr=subprocess.STDOUT,
            cwd=cookbookDir
        )
        subprocess.call(['rm', localCookbook],
            stdout=FNULL,
            stderr=subprocess.STDOUT,
            cwd=cookbookDir
        )
    except FileNotFoundError as e:
        print(e)

def get_deployment_status(deployment_id):
    response = opsworks.describe_deployments(DeploymentIds=[deployment_id])
    if len(response['Deployments']) == 1:
        return response['Deployments'][0]['Status']
    return 'failed'

def wait_for_deployment(deployment_id):
    status = 'failed'
    while True:
        status = get_deployment_status(deployment_id)
        if status in ['successful', 'failed']:
            break
        sleep(5)
    return status

def update_custom_cookbooks(stack):
    print('...Updating custom cookbooks [stack="'+stack['Name']+'"]')
    response = opsworks.create_deployment(
        StackId=stack['StackId'],
        Command={'Name': 'update_custom_cookbooks'}
    )
    deployment_id = response['DeploymentId']
    return wait_for_deployment(deployment_id)


def setup(stack):
    print('...Running setup command [stack="'+stack['Name']+'"]')
    response = opsworks.create_deployment(
        StackId=stack['StackId'],
        Command={'Name': 'setup'}
    )
    deployment_id = response['DeploymentId']
    return wait_for_deployment(deployment_id)

def deploy_app(stack, app):
    print('...Deploying [stack="'+stack['Name']+'" app="'+app['Name']+'"]')
    response = opsworks.create_deployment(
        StackId=stack['StackId'],
        AppId=app['AppId'],
        Command={'Name': 'deploy'}
    )
    deployment_id = response['DeploymentId']
    return wait_for_deployment(deployment_id)

def __cookbook_in_array(cb, cookbooks):
    return any(
        c['cookbook_key'] == cb['cookbook_key'] and c['bucket'] == cb['bucket'] \
        for c in cookbooks
    )

def deploy_stack(stack, built_cookbooks):
    # It's a bit inefficient to recall analyze_stack(), but we only built
    # cookbooks once so I'm calling it a win.
    apps, cookbook = analyze_stack(stack, output=False)

    # If this stack has a new cookbook
    if cookbook is not None:
        if __cookbook_in_array(cookbook, built_cookbooks):
            # Grabs a fresh copy of the cookbook on all instances in the stack
            try:
                if update_custom_cookbooks(stack) != 'successful':
                    raise Exception
            except:
                print("Update custom cookbooks command failed!")
                os._exit(1)
            try:
                # Re-runs the setup step for all layers
                if setup(stack) != 'successful':
                    raise Exception
            except:
                print("Setup command failed!")
                os._exit(1)

    # Deploy all apps for all stacks
    for app in apps:
        try:
            if deploy_app(stack, app) != 'successful':
                raise Exception
        except ClientError as e:
            print("Deployment failed!  Are there any running instances?")
            os._exit(1)
        except:
            print("Deployment failed!")
            os._exit(1)

def deploy():
    cookbooks_to_build = []
    try:
        stacks = opsworks.describe_stacks(StackIds=STACK_IDS)
    except ClientError as e:
        print(e)
        exit(1)

    # Collect and print stack info
    for stack in stacks['Stacks']:
        apps, cookbook = analyze_stack(stack)
        if cookbook is not None and 'local_sha' in cookbook:
            # We only build the cookbook if we don't have this version on S3
            if cookbook['remote_sha'] != cookbook['local_sha']:
                if not __cookbook_in_array(cookbook, cookbooks_to_build):
                    cookbooks_to_build.append(cookbook)
        print("")

    # Build each unique cookbook once in case it's used by more than one app
    for cookbook in cookbooks_to_build:
        build_and_deploy_cookbook(cookbook)

    deploy_threads = []
    # Deploy all apps for all stack and update cookbooks if needed
    for stack in stacks['Stacks']:
        t = threading.Thread(target=deploy_stack, args=(stack, cookbooks_to_build,))
        deploy_threads.append(t)
        t.start()

    for t in deploy_threads:
        t.join()

deploy()
