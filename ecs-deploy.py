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


class CLI(object):

    def __init__(self):
        # get args
        args = self._init_parser()

        # init boto3 client
        try:
            self.client = boto3.client('ecs')
        except ClientError as err:
            print('Failed to create boto3 client.\n%s' % err)
            sys.exit(1)

        # run script
        self._run_parser(args)

    def _init_parser(self):
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

    def _run_parser(self, args):
        if not args.get('task_definition'):
            service = self.get_service(args.get('service_name'), args.get('cluster'))
            arn = service['services'][0]['taskDefinition']
            name = arn.split('/')[1].split(':')[0]
            print(name)
            task_definition = self.get_task_definition(name)

        else:
            task_definition = self.get_task_definition(args.get('task_definition'))

        print(task_definition)
        task_definition = self.register_task_definition(task_definition, args.get('image'))
        print(task_definition)

        if task_definition:
            if not self.update_service(args.get('cluster'), args.get('service_name'), args.get('task_definition')):
                sys.exit(1)
            # wait and make sure things worked
        else:
            sys.exit(1)

    def get_service(self, service, cluster):
        """
        Gets info about service

        See all parameters for boto3 client's `describe_services()` here:
        https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#\
        ECS.Client.describe_services
        """
        try:
            response = self.client.describe_services(
                cluster=cluster,
                services=[service]
            )
            return response

        except ClientError as err:
            print('Failed to retrieve task definition.\n%s' % err)
        return False

    def update_service(self, service, cluster, task_definition):
        """
        Registers a new ECS Task definition

        See all parameters for boto3 client's `update_service()` here:
        http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.\
        Client.update_service
        """
        try:
            response = self.client.update_service(
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
            print('Failed to update the stack.\n%s' % err)
        return False

    def get_task_definition(self, task_definition_name):
        """
        Pulls down existing taskDefinition

        See all parameters for boto3 client's `describe_task_definition()` here:
        https://boto3.readthedocs.io/en/latest/reference/services/ecs.html#\
        ECS.Client.describe_task_definition
        """
        try:
            response = self.client.describe_task_definition(
                taskDefinition=task_definition_name
            )
            return response['taskDefinition']

        except ClientError as err:
            print('Failed to retrieve task definition.\n%s' % err)
        return False

    def register_task_definition(self, task_definition, image):
        """
        Registers a new ECS Task definition

        See all parameters for boto3 client's `register_task_definition()` here:
        http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.\
        Client.register_task_definition
        """
        task_definition['image'] = image
        try:
            response = self.client.register_task_definition(
                family=task_definition['family'],
                containerDefinitions=task_definition['containerDefinitions']
            )
            return response['taskDefinition']

        except ClientError as err:
            print('Failed to update the stack.\n%s' % err)
        except IOError as err:
            print('Failed to access %s.\n%s' % (definition, err))
        except KeyError as err:
            print('Unable to retrieve taskDefinitionArn key.\n%s' % err)
        return False


if __name__ == '__main__':
    CLI()
