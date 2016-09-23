import pytest
import boto3
from moto import mock_ecs


@mock_ecs
def test_init():
    client = boto3.client('ecs')

    mock_cluster = client.create_cluster(clusterName='mock_cluster')

    mock_task = client.register_task_definition(
        family='mock_task',
        taskRoleArn='string',
        networkMode='none',
        containerDefinitions=[
            {
                'name': 'string',
                'image': 'string',
                'cpu': 123,
                'memory': 123,
                'memoryReservation': 123,
                'links': [
                    'string',
                ],
                'portMappings': [
                    {
                        'containerPort': 123,
                        'hostPort': 123,
                        'protocol': 'tcp'
                    },
                ],
                'essential': True,
                'entryPoint': [
                    'string',
                ],
                'command': [
                    'string',
                ],
                'environment': [
                    {
                        'name': 'string',
                        'value': 'string'
                    },
                ],
                'mountPoints': [
                    {
                        'sourceVolume': 'string',
                        'containerPath': 'string',
                        'readOnly': True
                    },
                ],
                'volumesFrom': [
                    {
                        'sourceContainer': 'string',
                        'readOnly': True
                    },
                ],
                'hostname': 'string',
                'user': 'string',
                'workingDirectory': 'string',
                'disableNetworking': True,
                'privileged': True,
                'readonlyRootFilesystem': True,
                'dnsServers': [
                    'string',
                ],
                'dnsSearchDomains': [
                    'string',
                ],
                'extraHosts': [
                    {
                        'hostname': 'string',
                        'ipAddress': 'string'
                    },
                ],
                'dockerSecurityOptions': [
                    'string',
                ],
                'dockerLabels': {
                    'string': 'string'
                },
                'ulimits': [
                    {
                        'name': 'core',
                        'softLimit': 123,
                        'hardLimit': 123
                    },
                ],
                'logConfiguration': {
                    'logDriver': 'json-file',
                    'options': {
                        'string': 'string'
                    }
                }
            },
        ],
        volumes=[
            {
                'name': 'string',
                'host': {
                    'sourcePath': 'string'
                }
            },
        ]
    )

    mock_service = client.create_service(cluster='mock_cluster',
                                         serviceName='mock_service',
                                         taskDefinition='mock_task',
                                         desiredCount=1)


@mock_ecs
def test_something():
    # client.list_services(cluster='fake')
    # conn = boto3.connect_ecs

    assert True
