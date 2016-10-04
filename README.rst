=============
ecs-deploy.py
=============

.. image:: https://img.shields.io/pypi/v/ecs-deploy-py.svg
    :target: https://pypi.python.org/pypi/ecs-deploy-py

.. image:: https://travis-ci.org/cuttlesoft/ecs-deploy.py.svg?branch=master
	:target: https://travis-ci.org/cuttlesoft/ecs-deploy.py

.. image:: https://coveralls.io/repos/github/cuttlesoft/ecs-deploy.py/badge.svg
    :target: https://coveralls.io/github/cuttlesoft/ecs-deploy.py

-----

Python script to instigate an automatic blue/green deployment using the Task Definition and Service entities in Amazon's ECS.

Usage
-----

The script is installed as an executable with::

		$ pip install ecs-deploy-py

To run the script::

		$ ecs-deploy-py <args>

.. code-block::

	Either one of the following is required:
		 -n | --service-name     Name of service to deploy
		 -d | --task-definition  Name of task definition to deploy
 	Required arguments:
		 -k | --aws-access-key        AWS Access Key ID. May also be set as environment variable AWS_ACCESS_KEY_ID
		 -s | --aws-secret-key        AWS Secret Access Key. May also be set as environment variable AWS_SECRET_ACCESS_KEY
		 -r | --region                AWS Region Name. May also be set as environment variable AWS_DEFAULT_REGION
		 -p | --profile               AWS Profile to use - If you set this aws-access-key, aws-secret-key and region are needed
		 -c | --cluster               Name of ECS cluster
		 -i | --image                 Name of Docker image to run, ex: repo/image:latest
                                        Format: [domain][:port][/repo][/][image][:tag]
                                        Examples: mariadb, mariadb:latest, silintl/mariadb, silintl/mariadb:latest, private.registry.com:8000/repo/image:tag
	Optional arguments:
		 -D | --desired-count    The number of instantiations of the task to place and keep running in your service.
		 -m | --min              minumumHealthyPercent: The lower limit on the number of running tasks during a deployment.
		 -M | --max              maximumPercent: The upper limit on the number of running tasks during a deployment.
		 -t | --timeout          Default is 90s. Script monitors ECS Service for new task definition to be running.
		 -v | --verbose          Verbose output

    Examples:
    Simple (Using env vars for AWS settings):

    	$ ecs-deploy-py -c production1 -n doorman-service -i docker.repo.com/doorman:latest

    All options:

    	$ ecs-deploy-py -k ABC123 -s SECRETKEY -r us-east-1 -c production1 -n doorman-service -i docker.repo.com/doorman -m 50 -M 100 -t 240 -D 2 -v

    Using profiles (for STS delegated credentials, for instance):

    	$ ecs-deploy-py -p PROFILE -c production1 -n doorman-service -i docker.repo.com/doorman -m 50 -M 100 -t 240 -v

    Notes:
    	- If a tag is not found in image, it will default the tag to "latest"


About
-----
In EC2 Container Service, the relationship of containers which together provide a useful application (e.g. a database, \
web frontend, and perhaps some for maintenance/cron) is specified in a Task Definition. The Task Definition then acts a \
sort of template for actually running the containers in that group. That resulting group of containers is known as a Task.

Task Definitions are automatically version controlled---the actual name of a Task Definition is composed of two parts, \
the Family name, and a version number, like so: ``phpMyAdmin:3``.

Amazon uses another configuration entity, Services, to manage the number of Tasks running at any given time. As Tasks are \
just instantiations of Task Definitions, a Service is just a binding between a specified revision of a Task Definition, \
and the number of Tasks which should be run from it.

Conveniently, Amazon allows this binding to be updated, either to change the number of Tasks running or to change the Task \
Definition they are built from. In the former case, the Service will respond by building or killing Tasks to bring the \
count to specifications. In the latter case, however, it will do a blue/green deployment, that is, before killing any of \
the old Tasks, it will first ensure that a new Task is brought up and ready to use, so that there is no loss of service.

Consequently, all that is needed to deploy a new version of an application is to update the Service which is running its \
Tasks to point at a new version of the Task Definition. ecs-deploy uses the python aws utility to do this. It:

 - Pulls the JSON representation of the in-use Task Definition
 - Edits it
 - Defines a new version, with the changes
 - Updates the Service to use the new version
 - Waits, querying Amazon's API to make sure that the Service has been able to create a new Task

The second step merits more explanation: since a Task Definition [may] define multiple containers, the question arises, \
"what must be changed to create a new revision?" Empirically, the surprising answer is nothing; Amazon allows you to create \
a new but identical version of a Task Definition, and the Service will still do a blue/green deployment of identical tasks.

Nevertheless, since the system uses docker, the assumption is that improvements to the application are built into its \
container images, which are then pushed into a repository (public or private), to then be pulled down for use by ECS. This \
script therefore uses the specified image parameter as a modification key to change the tag used by a container's image. It \
looks for images with the same repository name as the specified parameter, and updates its tag to the one in the specified parameter.

This script inspired by: SIL International's `ecs-deploy`_.

.. _ecs-deploy: https://github.com/silinternational/ecs-deploy

Contributing
------------
If you're interested in contributing to ecs-deploy.py, get started by creating an issue `here`_. Thanks!

.. _here: https://github.com/cuttlesoft/ecs-deploy.py/issues
