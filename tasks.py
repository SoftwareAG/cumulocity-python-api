# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from invoke import task

import util.microservice_util as ms_util


@task(help={
    'scope': ("Which source directory to check, can be one of 'c8y_api', "
              "'tests', 'integration_tests' or 'all'. Default: 'all'")
})
def lint(c, scope='all'):
    """Run PyLint."""
    if scope == 'all':
        scope = 'c8y_api c8y_tk tests integration_tests samples'
    c.run(f'pylint --rcfile pylintrc --fail-under=9 {scope}')


@task
def build(c):
    """Build the module.

    This will create a distributable wheel (.whl) file.
    """
    c.run('python -m build')


@task(help={
    'clean': "Whether to clean the output before generation."
})
def build_docs(c, clean=False):
    """Build the documentation (HTML)."""
    dist_dir = 'dist/docs'
    docs_dir = 'docs'
    if clean:
        c.run(f'sphinx-build -M clean "{docs_dir}"  "{dist_dir}"')
    c.run(f'sphinx-build -M html "{docs_dir}"  "{dist_dir}"')


@task(help={
    'sample': "Which sample to build.",
    'name': "Microservice name. Defaults to sample name.",
    "version": "Microservice version. Defaults to '1.0.0'.",
})
def build_ms(c, sample, name=None, version='1.0.0'):
    """Build a Cumulocity microservice binary for upload.

    This will build a ready to deploy Cumulocity microservice from a sample
    file within the `samples` folder. Any sample Python script can be used
    (if it implements microservice logic).

    By default, uses the file name without .py extension as name. The built
    microservice will use a similar name, following Cumulocity guidelines.
    """
    sample_name = ms_util.format_sample_name(sample)
    c.run(f'samples/build.sh {sample_name} {version} {name if name else ""}')


@task(help={
    'sample': "Which sample to register."
})
def register_ms(_, sample):
    """Register a sample as microservice at Cumulocity."""
    ms_util.register_microservice(ms_util.format_sample_name(sample))


@task(help={
    'sample': "Which sample to unregister."
})
def unregister_ms(_, sample):
    """Unregister a sample microservice from Cumulocity."""
    ms_util.unregister_microservice(ms_util.format_sample_name(sample))


@task(help={
    'sample': "Which sample to register."
})
def get_credentials(_, sample):
    """Unregister a sample microservice from Cumulocity."""
    tenant, user, password = ms_util.get_credentials(ms_util.format_sample_name(sample))
    print(f"Tenant:    {tenant}\n"
          f"Username:  {user}\n"
          f"Password:  {password}")


@task(help={
    'sample': "Which sample to create a .env file for."
})
def create_env(_, sample):
    """Create a sample specific .env-{sample_name} file using the
    credentials of a corresponding microservice registered at Cumulocity."""
    sample_name = ms_util.format_sample_name(sample)
    tenant, user, password = ms_util.get_credentials(sample_name)
    with open(f'.env-{sample_name}', 'w', encoding='UTF-8') as f:
        f.write(f'C8Y_TENANT={tenant}\n'
                f'C8Y_USER={user}\n'
                f'C8Y_PASSWORD={password}\n')
