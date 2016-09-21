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


class CLI(object):
    def __init__(self):
        # get args
        self.args = self._init_parser()

        # init boto3 client
        try:
            self.client = boto3.client('ecs')
        except ClientError as err:
            print('Failed to create boto3 client.\n%s' % err)
            sys.exit(1)

        if not (self.args.get('task_definition') or self.args.get('service_name')):
            print('Either task-definition or service-name must be provided.')
            sys.exit(1)

        # run script
        self._run_parser()

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

    def _run_parser(self):
        self.cluster = self.args.get('cluster')
        self.task_definition_name = self._task_definition_name()
        self.service_name = self._service_name()

        task_definition_kwargs = {'taskDefinition': self.task_definition_name}
        task_definition = self.client_fn('describe_task_definition',
                                         **task_definition_kwargs)['taskDefinition']

        # TODO: DO THIS RIGHT
        # iteritems() in Python 2 == items() in Python 3
        try:
            given_args = {arg_name: arg for arg_name, arg in self.args.items() if arg}
        except:
            given_args = {arg_name: arg for arg_name, arg in self.args.iteritems() if arg}

        register_kwargs = {
            'family': task_definition['family'],
            'containerDefinitions': task_definition['containerDefinitions']
        }
        new_task_definition = self.client_fn('register_task_definition', **register_kwargs)['taskDefinition']

        update_kwargs = {
            'cluster': self.cluster,
            'service': self.service_name,
            'taskDefinition': new_task_definition['family']
        }
        if task_definition:
            # print(client_fn(client.update_service, **kwargs)['service']['taskDefinition'])
            if not self.client_fn('update_service', **update_kwargs):
                sys.exit(1)
            # wait and make sure things worked
        else:
            sys.exit(1)

    def _task_definition_name(self):
        if self.args.get('task_definition'):
            task_definition_name = self.args.get('task_definition')

        elif self.args.get('service_name'):
            kwargs = {
                'services': [self.args.get('service_name')],
                'cluster': self.cluster
            }
            service = self.client_fn('describe_services', **kwargs)
            arn = service['services'][0]['taskDefinition']
            task_definition_name = arn.split('/')[1].split(':')[0]

        else:
            # TODO: FAIL
            pass

        return task_definition_name

    def _service_name(self):
        if self.args.get('service_name'):
            service_name = self.args.get('service_name')

        elif self.args.get('task_definition'):
            kwargs = {'cluster': self.cluster}
            # for service in services['serviceArns']:
            #     if self.task_definition_name in service:
            #         service_name = service.split('/')[1].split(':')[0]
            serviceArns = self.client_fn('list_services', **kwargs)['serviceArns']
            service = [s for s in serviceArns if self.task_definition_name in s][0]
            service_name = service.split('/')[1].split(':')[0]

        else:
            # TODO: FAIL
            pass

        return service_name

    def client_fn(self, fn, **kwargs):
        try:
            response = getattr(self.client, fn)(**kwargs)
            return response

        except ClientError as e:
            print('ClientError: %s' % e)
            sys.exit(1)
        except Exception as e:
            print('Exception: %s' % e)
            sys.exit(1)

if __name__ == '__main__':
    CLI()
