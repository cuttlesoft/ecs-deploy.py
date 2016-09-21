# -*- coding: utf-8 -*-
"""
    ecs-deploy.py
    ~~~~~~~~~~~~~
    deployment script for AWS ECS
"""

from __future__ import print_function
import os
import sys
import json
import argparse
import boto3
from botocore.exceptions import ClientError


def main():
    # get args
    args = _init_parser()

    # init boto3 client
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print('Failed to create boto3 client.\n%s' % err)
        sys.exit(1)

    if not (args.get('task_definition') or args.get('service_name')):
        print('Either task-definition or service-name must be provided.')
        sys.exit(1)

    # run script
    _run_parser(client, args)


def _init_parser():
    parser = argparse.ArgumentParser(
        description='AWS ECS Deployment Script',
        usage='''ecs-deploy.py [<args>]
        ''')

    # REQUIRED ARGS : AT LEAST ONE

    parser.add_argument(
        '-n',
        '--service-name',
        help='Name of service to deploy (either service-name or task-definition is required)')

    parser.add_argument(
        '-d',
        '--task-definition',
        nargs='?',
        help='Name of task definition to deploy (either task-definition or service-name is required)')

    # REQUIRED ARGS : AT LEAST SOMEWHERE

    parser.add_argument(
        '-k',
        '--aws-access-key',
        help='AWS Access Key ID. May also be set as environment variable AWS_ACCESS_KEY_ID')

    parser.add_argument(
        '-s',
        '--aws-secret-key',
        help='AWS Secret Access Key. May also be set as environment variable AWS_SECRET_ACCESS_KEY')

    parser.add_argument(
        '-r',
        '--region',
        help='AWS Region Name. May also be set as environment variable AWS_DEFAULT_REGION')

    # REQUIRED ARGS : MAYBE NOT REQUIRED

    parser.add_argument(
        '-p',
        '--profile',
        help='AWS Profile to use (if you set this aws-access-key, aws-secret-key and region are needed)')

    parser.add_argument(
        '--aws-instance-profile',
        action='store_true',
        help='Use the IAM role associated with this instance')

    # REQUIRED ARGS

    parser.add_argument(
        '-c',
        '--cluster',
        required=True,
        help='Name of ECS cluster')

    parser.add_argument(
        '-i',
        '--image',
        required=True,
        help='Name of Docker image to run, ex: repo/image:latest\nFormat: [domain][:port][/repo][/][image][:tag]\nExamples: mariadb, mariadb:latest, silintl/mariadb,\nsilintl/mariadb:latest, private.registry.com:8000/repo/image:tag')

    # OPTIONAL ARGUMENTS

    parser.add_argument(
        '-D',
        '--desired-count',
        type=int,
        help='The number of instantiations of the task to place and keep running in your service.')

    parser.add_argument(
        '-m',
        '--min',
        type=int,
        help='minumumHealthyPercent: The lower limit on the number of running tasks during a deployment.')

    parser.add_argument(
        '-M',
        '--max',
        type=int,
        help='maximumPercent: The upper limit on the number of running tasks during a deployment.')

    parser.add_argument(
        '-t',
        '--timeout',
        help='Default is 90s. Script monitors ECS Service for new task definition to be running.')

    parser.add_argument(
        '-e',
        '--tag-env-var',
        help='Get image tag name from environment variable. If provided this will override value specified in image name argument.')

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Verbose output')

    parser.add_argument(
        '--max-definitions',
        type=int,
        help='Number of Task Definition Revisions to persist before deregistering oldest revisions.')

    args = parser.parse_args(sys.argv[1:])
    return vars(args)


def _run_parser(client, args):
    cluster = args.get('cluster')

    if args.get('task_definition'):
        task_definition_name = args.get('task_definition')

    elif args.get('service_name'):
        kwargs = {
            'services': [args.get('service_name')],
            'cluster': cluster
        }
        service = update_thing(client.describe_services, **kwargs)
        arn = service['services'][0]['taskDefinition']
        task_definition_name = arn.split('/')[1].split(':')[0]

    kwargs = {
        'taskDefinition': task_definition_name
    }
    task_definition = update_thing(client.describe_task_definition, **kwargs)['taskDefinition']

    for service in client.list_services(cluster=cluster)['serviceArns']:
        if task_definition['family'] in service:
            service_name = service.split('/')[1].split(':')[0]

    kwargs = {
        'family': task_definition['family'],
        'containerDefinitions': task_definition['containerDefinitions']
    }
    task_definition = update_thing(client.register_task_definition, **kwargs)['taskDefinition']

    kwargs = {
        'cluster': cluster,
        'service': service_name,
        'taskDefinition': task_definition['family']
    }
    if task_definition:
        # print(update_thing(client.update_service, **kwargs)['service']['taskDefinition'])
        if not update_thing(client.update_service, **kwargs):
            sys.exit(1)
        # wait and make sure things worked
    else:
        sys.exit(1)


def update_thing(func, **kwargs):
    response = func(**kwargs)
    return response


if __name__ == '__main__':
    main()
