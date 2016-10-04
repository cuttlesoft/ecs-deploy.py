# -*- coding: utf-8 -*-
"""
    setup.py
    ~~~~
"""
import sys
import os

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


def get_requirements(suffix=''):
    with open('requirements%s.txt' % suffix) as f:
        rv = f.read().splitlines()
    return rv


class PyTest(TestCommand):
    test_package_name = 'ecs_deploy'

    def finalize_options(self):
        TestCommand.finalize_options(self)
        _test_args = [
            '--verbose',
            '--ignore=build',
            '--cov', 'ecs_deploy',
            '--cov-report', 'term-missing',
            '--pep8',
            '--cache-clear'
        ]
        extra_args = os.environ.get('PYTEST_EXTRA_ARGS')
        if extra_args is not None:
            _test_args.extend(extra_args.split())
        self.test_args = _test_args
        self.test_suite = True

    def run_tests(self):
        import pytest
        from pkg_resources import normalize_path, _namespace_packages

        if sys.version_info >= (3,) and getattr(self.distribution,
                                                'use_2to3', False):
            module = self.test_package_name
            if module in _namespace_packages:
                del_modules = []
                if module in sys.modules:
                    del_modules.append(module)
                module += '.'
                for name in sys.modules:
                    if name.startswith(module):
                        del_modules.append(name)
                map(sys.modules.__delitem__, del_modules)

            ei_cmd = self.get_finalized_command('egg_info')

            self.test_args.append(normalize_path(ei_cmd.egg_base))

        errno = pytest.main(self.test_args)
        sys.exit(errno)


extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

setup(
    name='ecs-deploy-py',
    version='0.1.2',
    url='http://github.com/cuttlesoft/ecs-deploy.py',
    download_url='https://github.com/cuttlesoft/ecs-deploy.py/tarball/0.1.2',
    license='MIT',
    author='Cuttlesoft, LLC',
    author_email='engineering@cuttlesoft.com',
    description='Python script to instigate an automatic blue/green \
    deployment using Task Definition and Service entities in Amazon\'s ECS',
    long_description=open('README.rst').read() + '\n\n',
    packages=find_packages(),
    py_modules=['ecs_deploy'],
    zip_safe=False,
    platforms='any',
    install_requires=get_requirements(),
    package_data={
        '': ['*.txt']
    },
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'],
    entry_points={
        'console_scripts': [
            'ecs-deploy-py = ecs_deploy:CLI'
        ]
    }
)
