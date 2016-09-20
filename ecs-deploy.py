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


def new_task_definition(family, definition, image):
    """
    Registers a new ECS Task definition
    """
    try:
        client = boto3.client('ecs')
    except ClientError as err:
        print("Failed to create boto3 client.\n" + str(err))
        return False

    with open(definition) as definition:
        task_definition = json.load(definition)

    task_definition['image'] = image
    try:
        """
        see all parameters here:
        http://boto3.readthedocs.io/en/latest/reference/services/ecs.html#ECS.\
        Client.register_task_definition
        """
        response = client.register_task_definition(
            family=family,
            containerDefinitions=[task_definition]
        )
        return response['taskDefinition']['taskDefinitionArn']
    except ClientError as err:
        print("Failed to update the stack.\n" + str(err))
        return False
    except IOError as err:
        print("Failed to access " + definition + ".\n" + str(err))
        return False
    except KeyError as err:
        print("Unable to retrieve taskDefinitionArn key.\n" + str(err))
        return False


def update_service(cluster, service, count, task_definition, min_healthy,
                   max_healthy):
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
            desiredCount=count,
            taskDefinition=task_definition,
            deploymentConfiguration={
                # more information on the max and min healthy percentages
                # can be found here:
                # http://docs.aws.amazon.com/AmazonECS/latest/developerguide/update-service.html
                'maximumPercent': max_healthy,
                'minimumHealthyPercent': min_healthy
            }
        )
        return response
    except ClientError as err:
        print("Failed to update the stack.\n" + str(err))
        return False


def main():
    """
    Your favorite wrapper's favorite wrapper
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "definition",
        help="The path to an ECS Task Definition file in JSON format.  \
        See this for details:  http://docs.aws.amazon.com/AmazonECS/\
        latest/developerguide/task_definition_parameters.html#\
        container_definitions"
    )
    parser.add_argument("image",
                        help="The Docker Image to be used in the Task")
    parser.add_argument("count",
                        help="The desired number of Tasks to be running")
    parser.add_argument("min_healthy", help="The minimum number of healthy \
                        containers that should be running on the cluster")
    parser.add_argument("max_healthy", help="The maximum number of healthy \
                        containers that should be running on the cluster")
    args = parser.parse_args()

    cluster = os.getenv('ECS_CLUSTER_NAME')
    service = os.getenv('ECS_SERVICE_NAME')
    family = os.getenv('ECS_TASK_FAMILY_NAME')
    task_definition = new_task_definition(family, args.definition, args.image)

    if task_definition:
        if not update_service(cluster, service, int(args.count),
                              task_definition, int(args.min_healthy),
                              int(args.max_healthy)):
            sys.exit(1)
    else:
        sys.exit(1)


class CLI(object):

    def __init__(self):
        args = self._init_parser()
        # print(args)

        if not (args.get('service_name') or args.get('task_definition')):
            print('Either "service-name" or "task-definition" is required.')
        else:
            print('Service name: %s' % args.get('service_name'))
            print('Task definition: %s' % args.get('task_definition'))

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



if __name__ == "__main__":
    # main()
    CLI()
