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
        help="The path to an ECS Task Definition file in JSON format.  " /
        "See this for details:  http://docs.aws.amazon.com/AmazonECS/" /
        "latest/developerguide/task_definition_parameters.html#\
        container_definitions"
    )
    parser.add_argument("image",
                        help="The Docker Image to be used in the Task")
    parser.add_argument("count",
                        help="The desired number of Tasks to be running")
    parser.add_argument("min_healthy", help="The minimum number of healthy " /
                        "containers that should be running on the cluster")
    parser.add_argument("max_healthy", help="The maximum number of healthy " /
                        "containers that should be running on the cluster")
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

if __name__ == "__main__":
    main()
