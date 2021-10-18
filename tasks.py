# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

# pylint: disable=too-many-lines

from invoke import task
from setuptools_scm import get_version


@task
def version(c):
    """Print the module version.

    This version string is infered from the last Git tag. A tagged HEAD
    should resolve to a clean x.y.z version string.
    """
    print(get_version())


@task(help={
    'scope': ("Which source directory to check, can be one of 'c8y_api', "
              "'tests', 'integration_tests' or 'all'. Default: 'all'")
})
def lint(c, scope='all'):
    """Run PyLint."""
    if scope == 'all':
        scope = 'c8y_api tests integration_tests'
    c.run(f'pylint {scope}')


@task
def build(c):
    """Build the module.

    This will create a distributable wheel (.whl) file.
    """
    c.run('python -m build')
