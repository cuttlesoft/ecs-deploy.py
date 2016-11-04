#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    ecs-deploy.py
    ~~~~~~~~~~~~~
    deployment script for AWS ECS
"""

from __future__ import print_function
import sys
import time
import argparse
import boto3
from botocore.exceptions import ClientError


class CLI(object):
    def __init__(self):
        # get args
        self.args = self._init_parser()

        # init boto3 client
        try:
            # optional aws credentials overrides
            credentials = {}
            credentials = self._arg_kwargs(credentials, 'aws_access_key',
                                           'aws_access_key_id')
            credentials = self._arg_kwargs(credentials, 'aws_secret_key',
                                           'aws_secret_access_key')
            credentials = self._arg_kwargs(credentials, 'aws_region',
                                           'region_name')

            # init boto3 ecs client
            self.client = boto3.client('ecs', **credentials)
        except ClientError as err:
            print('Failed to create boto3 client.\n%s' % err)
            sys.exit(1)

        if not (self.args.get('task_definition') or
                self.args.get('service_name')):
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
            help='Name of service to deploy (either service-name or \
                task-definition is required)')

        parser.add_argument(
            '-d',
            '--task-definition',
            help='Name of task definition to deploy (either task-definition \
                or service-name is required)')

        # REQUIRED ARGS : AT LEAST SOMEWHERE

        parser.add_argument(
            '-k',
            '--aws-access-key',
            help='AWS Access Key ID. May also be set as environment variable \
                AWS_ACCESS_KEY_ID')

        parser.add_argument(
            '-s',
            '--aws-secret-key',
            help='AWS Secret Access Key. May also be set as environment \
                variable AWS_SECRET_ACCESS_KEY')

        parser.add_argument(
            '-r',
            '--aws-region',
            help='AWS Region Name. May also be set as environment variable \
                AWS_DEFAULT_REGION')

        # REQUIRED ARGS : MAYBE NOT REQUIRED

        parser.add_argument(
            '-p',
            '--profile',
            help='AWS Profile to use (if you set this aws-access-key, \
                aws-secret-key and region are needed)')

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
            '-l',
            '--container-image',
            action='append',
            required=True,
            help='Name of the container with the name of Docker image to run\
                \nFormat: \
                [container_name]=[domain][:port][/repo][/][image][:tag]\
                \nExamples: db=mariadb, database=mariadb:latest, \
                db=silintl/mariadb:latest, \
                my_container|private.registry.com:8000/repo/image:tag. \
                You can use this argument multiple times to replace images.')

        # OPTIONAL ARGUMENTS

        parser.add_argument(
            '-D',
            '--desired-count',
            type=int,
            help='The number of instantiations of the task to place and keep \
                running in your service.')

        parser.add_argument(
            '-m',
            '--min',
            type=int,
            help='minumumHealthyPercent: The lower limit on the number of \
                running tasks during a deployment.')

        parser.add_argument(
            '-M',
            '--max',
            type=int,
            help='maximumPercent: The upper limit on the number of running \
                tasks during a deployment.')

        parser.add_argument(
            '-t',
            '--timeout',
            help='Default is 90s. Script monitors ECS Service for new task \
                definition to be running.')

        parser.add_argument(
            '-e',
            '--tag-env-var',
            help='Get image tag name from environment variable. If provided \
                this will override value specified in image name argument.')

        parser.add_argument(
            '-v',
            '--verbose',
            action='store_true',
            help='Verbose output')

        parser.add_argument(
            '--max-definitions',
            type=int,
            help='Number of Task Definition Revisions to persist before \
                deregistering oldest revisions.')

        args = parser.parse_args(sys.argv[1:])
        return vars(args)

    def _run_parser(self):
        self.cluster = self.args.get('cluster')
        self.task_definition_name = self._task_definition_name()
        self.service_name = self._service_name()

        self.task_definition = self.client_fn(
            'describe_task_definition')['taskDefinition']
        print('Current task definition: %s' %
              self.task_definition['taskDefinitionArn'])

        self.new_task_definition = self.client_fn(
            'register_task_definition')['taskDefinition']
        print('New task definition: %s' %
              self.new_task_definition['taskDefinitionArn'])

        if self.task_definition:
            if not self.client_fn('update_service'):
                sys.exit(1)

            # loop for desired timeout
            timeout = self._int_or_none(self.args.get('timeout')) or 90
            started_at = time.time()
            while True:
                self.running_tasks = self.client_fn('list_tasks')['taskArns']

                if len(self.running_tasks) > 0:
                    described_tasks = self.client_fn('describe_tasks')['tasks']
                else:
                    described_tasks = []

                for task in described_tasks:
                    if task['taskDefinitionArn'] == \
                            self.new_task_definition['taskDefinitionArn']:
                        print('Service updated successfully, '
                              'new task definition running.')
                        return
                if time.time() > started_at + timeout:
                    print('ERROR: New task definition not running'
                          'within %d seconds' % timeout)
                    sys.exit(1)
                time.sleep(1)

        else:
            sys.exit(1)

    def _int_or_none(self, value):
        if type(value) == str and value.isdigit():
            return int(value)
        return None

    def _task_definition_name(self):
        if self.args.get('task_definition'):
            return self.args.get('task_definition')

        # use 'service_name' with describe_services() to get task definition
        service = self.client_fn('describe_services')
        arn = service['services'][0]['taskDefinition']
        return arn.split('/')[1].split(':')[0]

    def _service_name(self):
        if self.args.get('service_name'):
            return self.args.get('service_name')

        # use 'task_definition' with list_services() to get service name
        serviceArns = self.client_fn('list_services')['serviceArns']
        service = [s for s in serviceArns if self.args.get('task_definition')
                   in s][0]
        return service.split('/')[1].split(':')[0]

    def _arg_kwargs(self, kwargs, arg_name, alt_name=None):
        # add specified arg to kwargs if it exists, return kwargs
        if self.args.get(arg_name):
            kwarg_name = alt_name or arg_name
            kwargs[kwarg_name] = self.args.get(arg_name)
        return kwargs

    def client_kwargs(self, fn):
        kwargs = {}

        if fn == 'list_services':
            kwargs['cluster'] = self.cluster

        elif fn == 'describe_services':
            kwargs['cluster'] = self.cluster
            kwargs['services'] = [self.args.get('service_name')]

        elif fn == 'describe_task_definition':
            kwargs['taskDefinition'] = self.task_definition_name

        elif fn == 'register_task_definition':
            kwargs['family'] = self.task_definition['family']
            kwargs['containerDefinitions'] = \
                self.task_definition['containerDefinitions']

            # optional kwargs from args
            for ci in self.args.get('container_image'):
                ci_container_name, ci_image = ci.split('=')
                container_found = False

                for cd in kwargs['containerDefinitions']:
                    if cd['name'] == ci_container_name:
                        cd['image'] = ci_image
                        container_found = True

                if not container_found:
                    print('Container %s not found in the task definition %s' %
                          (ci_container_name,
                           self.task_definition['taskDefinitionArn']))
                    sys.exit(1)

        elif fn == 'update_service':
            kwargs['cluster'] = self.cluster
            kwargs['service'] = self.service_name
            kwargs['taskDefinition'] = self.new_task_definition['family']
            # optional kwargs from args
            deployment_config = {}
            deployment_config = self._arg_kwargs(deployment_config, 'min',
                                                 'minimumHealthyPercent')
            deployment_config = self._arg_kwargs(deployment_config, 'max',
                                                 'maximumPercent')
            kwargs['deploymentConfiguration'] = deployment_config
            kwargs = self._arg_kwargs(kwargs, 'desired_count')

        elif fn == 'list_tasks':
            kwargs['cluster'] = self.cluster
            kwargs['serviceName'] = self.service_name
            kwargs['desiredStatus'] = 'RUNNING'

        elif fn == 'describe_tasks':
            kwargs['cluster'] = self.cluster
            kwargs['tasks'] = self.running_tasks

        return kwargs

    def client_fn(self, fn):
        try:
            kwargs = self.client_kwargs(fn)
            response = getattr(self.client, fn)(**kwargs)
            return response

        except ClientError as e:
            print('ClientError: %s' % e)
            sys.exit(1)
        except Exception as e:
            print('Exception: %s' % e)
            sys.exit(1)


def main():
    CLI()


if __name__ == '__main__':
    main()
