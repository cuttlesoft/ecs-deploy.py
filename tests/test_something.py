import pytest
import boto3
from moto import mock_ecs


@mock_ecs
def test_something():
    client = boto3.client('ecs')

    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    print(client.list_services(cluster='vanguard'))

    assert False
