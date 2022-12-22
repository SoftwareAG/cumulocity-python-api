# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

import json
import zipfile

from dotenv import load_dotenv

from c8y_api.app import SimpleCumulocityApp
from c8y_api.model import Application

_DIST_DIR = 'dist'


def format_sample_name(name: str) -> str:
    """Format a name as sample name (underscores instead of hyphens)."""
    return name.replace('-', '_')


def format_application_name(name: str) -> str:
    """Format a name as application name (hyphens instead of underscores)."""
    return name.replace('_', '-')


def register_microservice(sample_name: str):
    """ Register a microservice at Cumulocity.

    The Cumulocity connection information is taken from environment files
    (.env and .env-SAMPLE-NAME) located in the working directory.

    Args:
        sample_name (str):  The name of the sample to use (file name
            without .py extension)

    """
    application_name = format_application_name(sample_name)
    load_dotenv()
    c8y = SimpleCumulocityApp()

    # Verify this application is not registered, yet
    if c8y.applications.get_all(name=application_name):
        raise ValueError(f"Microservice application named '{application_name}' seems to be already registered.")

    # Read prepared binary .zip, extract manifest and parse
    zip_path = f'{_DIST_DIR}/samples/{sample_name}/{application_name}.zip'
    zip_file = zipfile.ZipFile(zip_path, 'r')
    manifest_json = json.loads(zip_file.read('cumulocity.json'))

    # Create application stub in Cumulocity
    required_roles = manifest_json['requiredRoles']
    app = Application(c8y, name=application_name, key=f'{application_name}-key',
                      type=Application.MICROSERVICE_TYPE,
                      availability=Application.PRIVATE_AVAILABILITY,
                      required_roles=required_roles)
    app = app.create()

    print(f"Microservice application '{application_name}' created. (ID {app.id})")


def unregister_microservice(sample_name: str):
    """ Unregister a microservice from Cumulocity.

    The Cumulocity connection information is taken from environment files
    (.env and .env-SAMPLE-NAME) located in the working directory.

    Args:
        sample_name (str):  The name of the sample to use (file name
            without .py extension)

    Throws:
        LookupError  if a corresponding application cannot be found.
    """
    application_name = format_application_name(sample_name)
    load_dotenv()

    try:
        c8y = SimpleCumulocityApp()
        # read applications by name, will throw IndexError if there is none
        app = c8y.applications.get_all(name=application_name)[0]
        # delete by ID
        app.delete()
    except IndexError:
        raise LookupError(f"Cannot retrieve information for an application named '{application_name}'.")

    print(f"Microservice application '{application_name}' (ID {app.id}) deleted.")


def get_credentials(sample_name: str) -> (str, str):
    """ Get the bootstrap user credentials of a registered microservice.

    The Cumulocity connection information is taken from environment files
    (.env and .env-SAMPLE-NAME) located in the working directory.

    Args:
        sample_name (str):  The name of the sample to use (file name
            without .py extension)

    Returns:
        A pair (username, password) for the credentials.

    Throws:
        LookupError  if a corresponding application cannot be found.
    """
    application_name = format_application_name(sample_name)
    load_dotenv()

    try:
        c8y = SimpleCumulocityApp()
        # read applications by name, will throw IndexError if there is none
        app = c8y.applications.get_all(name=application_name)[0]
        # read bootstrap user details, parse and print
        user_json = c8y.get(f'/application/applications/{app.id}/bootstrapUser')
        return user_json['name'], user_json['password']
    except IndexError:
        raise LookupError(f"Cannot retrieve information for an application named '{application_name}'.")
