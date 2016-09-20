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


def main():
    """
    Your favorite wrapper's favorite wrapper
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("cluster",
                        help="The AWS cluster")
    parser.add_argument("service",
                        help="The AWS Service")
    parser.add_argument("definition_name",
                        help="The name of the AWS Task Definition")
    parser.add_argument("image",
                        help="The Docker Image to be used in the Task")
    # parser.add_argument("count",
    #                     help="The desired number of Tasks to be running")
    # parser.add_argument("min_healthy", help="The minimum number of healthy \
    #                     containers that should be running on the cluster")
    # parser.add_argument("max_healthy", help="The maximum number of healthy \
    #                     containers that should be running on the cluster")
    args = parser.parse_args()

    # cluster = os.getenv('ECS_CLUSTER_NAME')
    # service = os.getenv('ECS_SERVICE_NAME')
    # family = os.getenv('ECS_TASK_FAMILY_NAME')

    if args.definition_name:
        task_definition = get_task_definition(args.definition_name)

    elif args.service:
        task_definition = get_service_something(args.service, args.cluster)['services'][0]['taskDefinition'].split('/')[1].split(':')[0]

    else:
        print('Fail')
        sys.exit(1)

    print(task_definition)
    task_definition = new_task_definition(task_definition, args.image)
    print(task_definition)

    if task_definition:
        if not update_service(args.cluster, args.service, args.definition_name):
            sys.exit(1)
        # wait and make sure things worked
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
