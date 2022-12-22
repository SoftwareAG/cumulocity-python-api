# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from invoke import task
from setuptools_scm import get_version

import util.microservice_util as ms_util


@task
def show_version(_):
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
        scope = 'c8y_api tests integration_tests samples'
    c.run(f'pylint {scope}')


@task
def build(c):
    """Build the module.

    This will create a distributable wheel (.whl) file.
    """
    c.run('python -m build')


@task(help={
    'sample': "Which sample to build.",
    "version": "Microservice version. Defaults to '1.0.0'.",
})
def build_ms(c, sample, version='1.0.0'):
    """Build a Cumulocity microservice binary for upload.

    This will build a ready to deploy Cumulocity microservice from a sample
    file within the `samples` folder. Any sample Python script can be used
    (if it implements microservice logic).

    Use the file name without .py extension as name. The build microservice
    will use a similar name, following Cumulocity naming guidelines.
    """
    sample_name = ms_util.format_sample_name(sample)
    c.run(f'samples/build.sh {sample_name} {version}')


@task(help={
    'sample': "Which sample to register."
})
def register_ms(c, sample):
    """Register a sample as microservice at Cumulocity."""
    ms_util.register_microservice(ms_util.format_sample_name(sample))


@task(help={
    'sample': "Which sample to unregister."
})
def unregister_ms(c, sample):
    """Unregister a sample microservice from Cumulocity."""
    ms_util.unregister_microservice(ms_util.format_sample_name(sample))


@task(help={
    'sample': "Which sample to register."
})
def get_credentials(c, sample):
    """Unregister a sample microservice from Cumulocity."""
    user, password = ms_util.get_credentials(ms_util.format_sample_name(sample))
    print(f"Username:  {user}\n"
          f"Password:  {password}")


@task(help={
    'sample': "Which sample to create a .env file for."
})
def create_env(c, sample):
    """Create a sample specific .env-{sample_name} file using the
    credentials of a corresponding microservice registered at Cumulocity."""
    sample_name = ms_util.format_sample_name(sample)
    user, password = ms_util.get_credentials(sample_name)
    with open(f'.env-{sample_name}', 'w') as f:
        f.write(f"C8Y_USER={user}\n"
                f"C8Y_PASSWORD={password}\n")
