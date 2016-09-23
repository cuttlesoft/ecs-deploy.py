import pytest
import mock
import boto3
from moto import mock_ecs

from ecs_deploy import CLI


class TestCLI(object):

    @mock_ecs
    def setUp(self):
        with mock.patch.object(CLI, '__init__') as mock_init:
            mock_init.return_value = None
            self.mock_cli = CLI()

        self.client = boto3.client('ecs')

        mock_cluster = self.client.create_cluster(clusterName='mock_cluster')

        mock_task = self.client.register_task_definition(
            family='mock_task',
            taskRoleArn='arn:aws:ecs:us-east-1:999999999999:task-definition/ \
                mock_task:99',
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

        mock_service = self.client.create_service(cluster='mock_cluster',
                                                  serviceName='mock_service',
                                                  taskDefinition='mock_task',
                                                  desiredCount=1
                                                  )

        self.mock_cli.args = {
            'cluster': mock_cluster['cluster']['clusterName'],
            'task_definition': mock_task['taskDefinition']['family'],
            'service_name': mock_service['service']['serviceName']
        }

        self.mock_cli.cluster = mock_cluster
        self.mock_cli.task = mock_task
        self.mock_cli.service = mock_service

        # return self.mock_task, self.mock_cluster, self.mock_service
        return self.mock_cli, self.client

    def test_task_definition_name_with_arg(self):
        mock_cli, client = self.setUp()
        assert mock_cli._task_definition_name() == \
            mock_cli.args['task_definition']

    def test_task_definition_name_without_arg(self):
        mock_cli, client = self.setUp()

        with mock.patch.object(mock_cli, 'client_fn') as mock_fn:
            mock_describe_services_response = {
                'services': [{
                    'taskDefinition': mock_cli.task['taskDefinition']
                    ['taskDefinitionArn']
                }]
            }
            mock_fn.return_value = mock_describe_services_response
            task_definition_name = mock_cli.args['task_definition']
            mock_cli.args['task_definition'] = None

            mock_task_name = mock_cli._task_definition_name()

            assert mock_task_name == task_definition_name
            mock_fn.assert_called_once_with('describe_services')

    def test_service_name_with_arg(self):
        mock_cli, client = self.setUp()
        assert mock_cli._service_name() == \
            mock_cli.args['service_name']

    # blasphemy
    # def test_service_name_without_arg(self):
    #     mock_cli, client = self.setUp()
    #
    #     with mock.patch.object(mock_cli, 'client_fn') as mock_fn:
    #         mock_list_services_response = client.list_services(
    #             cluster=mock_cli.args['cluster'])
    #         mock_fn.return_value = mock_list_services_response
    #         service_name = mock_cli.args['service_name']
    #         mock_cli.args['service_name'] = None
    #
    #         assert mock_cli._service_name() == service_name
