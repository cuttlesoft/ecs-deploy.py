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

        self.client = boto3.client('ecs', region_name='us-east-1')

        mock_cluster = self.client.create_cluster(clusterName='mock_cluster')

        mock_task = self.client.register_task_definition(
            family='mock_task',
            taskRoleArn='arn:aws:ecs:us-east-1:999999999999:task-definition/ \
                mock_task:99',
            networkMode='none',
            containerDefinitions=[
                {
                    'name': 'string',
                    'image': 'original_image',
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
                                                  serviceName='mock_task' +
                                                  '-service',
                                                  taskDefinition='mock_task',
                                                  desiredCount=1
                                                  )

        self.mock_cli.args = {
            'cluster': mock_cluster['cluster']['clusterName'],
            'task_definition': mock_task['taskDefinition']['family'],
            'service_name': mock_service['service']['serviceName'],
            'image': 'mock_image'
        }

        self.mock_cli.cluster = mock_cluster['cluster']
        self.mock_cli.task_definition = mock_task['taskDefinition']
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
                    'taskDefinition': mock_cli.task_definition
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

    def test_service_name_without_arg(self):
        mock_cli, client = self.setUp()

        with mock.patch.object(mock_cli, 'client_fn') as mock_fn:
            mock_list_services_response = {
                'serviceArns': [
                    mock_cli.service['service']['serviceArn']
                ]
            }
            mock_fn.return_value = mock_list_services_response
            service_name = mock_cli.args['service_name']
            mock_cli.args['service_name'] = None

            mock_service_name = mock_cli._service_name()

            assert mock_service_name == service_name
            mock_fn.assert_called_once_with('list_services')

    def test_arg_kwargs_add_arg(self):
        mock_cli, client = self.setUp()
        mock_kwargs = {}
        mock_cli._arg_kwargs(mock_kwargs, 'cluster')

        assert 'cluster' in mock_kwargs

    def test_arg_kwargs_without_arg(self):
        mock_cli, client = self.setUp()
        mock_kwargs = {}
        mock_cli._arg_kwargs(mock_kwargs, 'fake_arg')

        assert 'fake_arg' not in mock_kwargs

    def test_client_kwargs_with_list_services(self):
        mock_cli, client = self.setUp()
        mock_kwargs = mock_cli.client_kwargs('list_services')

        assert 'cluster' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']

    def test_client_kwargs_with_describe_services(self):
        mock_cli, client = self.setUp()
        mock_kwargs = mock_cli.client_kwargs('describe_services')

        assert 'cluster' in mock_kwargs
        assert 'services' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['services'][0] == mock_cli.args['service_name']

    def test_client_kwargs_with_describe_task_definition(self):
        mock_cli, client = self.setUp()
        mock_cli.task_definition_name = mock_cli.args['task_definition']
        mock_kwargs = mock_cli.client_kwargs('describe_task_definition')

        assert 'taskDefinition' in mock_kwargs
        assert mock_kwargs['taskDefinition'] == \
            mock_cli.args['task_definition']

    def test_client_kwargs_with_register_task_definition(self):
        mock_cli, client = self.setUp()
        mock_kwargs = mock_cli.client_kwargs('register_task_definition')

        assert 'family' in mock_kwargs
        assert 'containerDefinitions' in mock_kwargs
        assert mock_kwargs['containerDefinitions'][0]['image'] == \
            mock_cli.args['image']
        assert mock_kwargs['family'] == mock_cli.task_definition['family']

    def test_client_kwargs_with_update_service(self):
        mock_cli, client = self.setUp()
        mock_cli.new_task_definition = {
            'family': 'new_mock_task'
        }
        mock_cli.service_name = mock_cli.args['service_name']
        mock_kwargs = mock_cli.client_kwargs('update_service')

        assert 'cluster' in mock_kwargs
        assert 'service' in mock_kwargs
        assert 'taskDefinition' in mock_kwargs
        assert 'deploymentConfiguration' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['service'] == mock_cli.service_name
        assert mock_kwargs['taskDefinition'] == \
            mock_cli.new_task_definition['family']
        assert 'min' or 'minimumHealthyPercent' or 'max' or 'maximumPercent' \
            not in mock_kwargs['deploymentConfiguration']

    def test_client_kwargs_with_update_service_min(self):
        mock_cli, client = self.setUp()
        mock_cli.new_task_definition = {
            'family': 'new_mock_task'
        }
        mock_cli.service_name = mock_cli.args['service_name']
        mock_cli.args['min'] = '100'

        mock_kwargs = mock_cli.client_kwargs('update_service')

        assert 'cluster' in mock_kwargs
        assert 'service' in mock_kwargs
        assert 'taskDefinition' in mock_kwargs
        assert 'deploymentConfiguration' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['service'] == mock_cli.service_name
        assert mock_kwargs['taskDefinition'] == \
            mock_cli.new_task_definition['family']
        assert mock_kwargs['deploymentConfiguration']
        ['minimumHealthyPercent'] == mock_cli.args['min']
        assert 'max' or 'maximumPercent' not in \
            mock_kwargs['deploymentConfiguration']

    def test_client_kwargs_with_update_service_max(self):
        mock_cli, client = self.setUp()
        mock_cli.new_task_definition = {
            'family': 'new_mock_task'
        }
        mock_cli.service_name = mock_cli.args['service_name']
        mock_cli.args['max'] = '200'

        mock_kwargs = mock_cli.client_kwargs('update_service')

        assert 'cluster' in mock_kwargs
        assert 'service' in mock_kwargs
        assert 'taskDefinition' in mock_kwargs
        assert 'deploymentConfiguration' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['service'] == mock_cli.service_name
        assert mock_kwargs['taskDefinition'] == \
            mock_cli.new_task_definition['family']
        assert mock_kwargs['deploymentConfiguration']
        ['maximumPercent'] == mock_cli.args['max']
        assert 'min' or 'minimumHealthyPercent' not in \
            mock_kwargs['deploymentConfiguration']

    def test_client_kwargs_with_update_service_desired_count(self):
        mock_cli, client = self.setUp()
        mock_cli.new_task_definition = {
            'family': 'new_mock_task'
        }
        mock_cli.service_name = mock_cli.args['service_name']
        mock_cli.args['desired_count'] = '50'

        mock_kwargs = mock_cli.client_kwargs('update_service')

        assert 'cluster' in mock_kwargs
        assert 'service' in mock_kwargs
        assert 'taskDefinition' in mock_kwargs
        assert 'deploymentConfiguration' in mock_kwargs
        assert 'desired_count' in mock_kwargs
        assert mock_kwargs['desired_count'] == mock_cli.args['desired_count']
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['service'] == mock_cli.service_name
        assert mock_kwargs['taskDefinition'] == \
            mock_cli.new_task_definition['family']
        assert 'min' or 'minimumHealthyPercent' or 'max' or 'maximumPercent' \
            not in mock_kwargs['deploymentConfiguration']

    def test_client_kwargs_with_list_tasks(self):
        mock_cli, client = self.setUp()
        mock_cli.service_name = mock_cli.args['service_name']

        mock_kwargs = mock_cli.client_kwargs('list_tasks')

        assert 'cluster' in mock_kwargs
        assert 'serviceName' in mock_kwargs
        assert 'desiredStatus' in mock_kwargs
        assert mock_kwargs['cluster']['clusterName'] == \
            mock_cli.args['cluster']
        assert mock_kwargs['serviceName'] == mock_cli.service_name
        assert mock_kwargs['desiredStatus'] == 'RUNNING'

    def test_client_kwargs_with_describe_tasks(self):
        mock_cli, client = self.setUp()
        mock_cli.service_name = mock_cli.args['service_name']

        with mock.patch.object(mock_cli, 'client_fn') as mock_fn:
            mock_list_tasks_response = {
                'taskArns': [
                    mock_cli.task_definition['taskDefinitionArn']
                ]
            }
            mock_fn.return_value = mock_list_tasks_response
            mock_kwargs = mock_cli.client_kwargs('describe_tasks')

            assert 'cluster' in mock_kwargs
            assert 'tasks' in mock_kwargs
            assert mock_kwargs['cluster']['clusterName'] == \
                mock_cli.args['cluster']
            assert mock_kwargs['tasks'] == mock_list_tasks_response['taskArns']

    def test_client_kwargs_with_describe_tasks(self):
        mock_cli, client = self.setUp()
        mock_cli.client = client

        with mock.patch.object(client, 'list_services',
                               return_value={'key': 'value'}) as mock_client:
            mock_cli.client_fn('list_services')
            mock_client.assert_called_once
