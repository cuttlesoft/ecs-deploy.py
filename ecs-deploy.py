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
import pprint
from botocore.exceptions import ClientError


def get_service_something(service, cluster):
    """
    Gets info about service
    """
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        """
        see all parameters here:
        https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#\
        ECS.Client.describe_services
        """
        response = client.describe_services(
            cluster=cluster,
            services=[service]
        )
        return response
    except ClientError as err:
        print("Failed to retrieve task definition.\n" + str(err))
        return False


def get_task_definition(definition_name):
    """
    Pulls down existing taskDefinition
    """
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        """
        see all parameters here:
        https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#\
        ECS.Client.describe_task_definition
        """
        response = client.describe_task_definition(
            taskDefinition=definition_name
        )
        return response['taskDefinition']
    except ClientError as err:
        print("Failed to retrieve task definition.\n" + str(err))
        return False


def new_task_definition(task_definition, image):
    """
    Registers a new ECS Task definition
    """
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    family = task_definition['family']
    task_definition['image'] = image
    try:
        """
        see all parameters here:
        http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.\
        Client.register_task_definition
        """
        response = client.register_task_definition(
            family=family,
            containerDefinitions=task_definition['containerDefinitions']
        )
        return response['taskDefinition']
    except ClientError as err:
        print("Failed to update the stack.\n" + str(err))
        return False
    except IOError as err:
        print("Failed to access " + definition + ".\n" + str(err))
        return False
    except KeyError as err:
        print("Unable to retrieve taskDefinitionArn key.\n" + str(err))
        return False


def update_service(cluster, service, task_definition):
    """
    Registers a new ECS Task definition
    """
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    try:
        """
        see all parameters here:
        http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.\
        Client.update_service
        """
        response = client.update_service(
            cluster=cluster,
            service=service,
            # desiredCount=count,
            taskDefinition=task_definition
            # deploymentConfiguration={
            #     # more information on the max and min healthy percentages
            #     # can be found here:
            #     # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/update-service.html
            #     'maximumPercent': max_healthy,
            #     'minimumHealthyPercent': min_healthy
            # }
        )
        return response
    except ClientError as err:
        print("Failed to update the stack.\n" + str(err))
        return False


class CLI(object):

    def __init__(self):
        args = self._init_parser()

        if not (args.get('service_name') or args.get('task_definition')):
            print('Either "service-name" or "task-definition" is required.')
        else:
            print('Service name: %s' % args.get('service_name'))
            print('Task definition: %s' % args.get('task_definition'))
            self._run_parser(args)

    def _init_parser(self):
        parser = argparse.ArgumentParser(
            description='AWS ECS Deployment Script',
            usage='''ecs-deploy.py [<args>]

Required:
    ...

Optional:
    ...

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
            help='Name of ECS cluster')

        parser.add_argument(
            '-i',
            '--image',
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

    def _run_parser(self, args):
        if not args.get('task_definition'):
            name = get_service_something(args.get('service_name'), args.get('cluster'))['services'][0]['taskDefinition'].split('/')[1].split(':')[0]
            print(name)
            task_definition = get_task_definition(name)

        else:
            task_definition = get_task_definition(args.get('task_definition'))

        print(task_definition)
        task_definition = new_task_definition(task_definition, args.get('image'))
        print(task_definition)

        if task_definition:
            if not update_service(args.get('cluster'), args.get('service_name'), args.get('task_definition')):
                sys.exit(1)
            # wait and make sure things worked
        else:
            sys.exit(1)


if __name__ == "__main__":
    CLI()
