# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

from typing import Generator, List, BinaryIO

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model._base import SimpleObject, CumulocityResource
from c8y_api.model._parser import SimpleObjectParser


class Application(SimpleObject):
    """Represent an instance of an application object in Cumulocity.

    Instances of this class are returned by functions of the corresponding
    API. Use this class to create new or update objects.

    See also: https://cumulocity.com/api/#tag/Application-API
    """
    _parser = SimpleObjectParser({
        '_u_name': 'name',
        '_u_type': 'type',
        '_u_key': 'key',
        '_u_availability': 'availability',
        'owner': 'owner',
        'manifest': 'manifest',
        '_u_roles': 'roles',
        '_u_required_roles': 'requiredRoles',
        '_u_breadcrumbs': 'breadcrumbs',
        '__u_content_security_policy': 'contentSecurityPolicy',
        '_u_dynamic_options_url': 'dynamicOptionsUrl',
        '__u_global_title': 'globalTitle',
        '_u_legacy': 'legacy',
        '_u_rightDrawer': 'rightDrawer',
        '_u_upgrade': 'upgrade'
    })
    _resource = '/application/applications'
    _accept = 'application/vnd.com.nsn.cumulocity.application+json'
    _not_updatable = ['owner']

    EXTERNAL_TYPE = "EXTERNAL"
    HOSTED_TYPE = "HOSTED"
    MICROSERVICE_TYPE = "MICROSERVICE"

    PRIVATE_AVAILABILITY = 'PRIVATE'
    MARKET_AVAILABILITY = 'MARKET'

    def __init__(self, c8y: CumulocityRestApi = None, name: str = None, key: str = None, type: str = None,
                 availability: str = None, context_path: str = None, manifest: dict = None,
                 roles: List[str] = None, required_roles: List[str] = None,
                 breadcrumbs: bool = None, content_security_policy: str = None,
                 dynamic_options_url: str = None, global_title: str = None,
                 legacy: bool = None, right_drawer: bool = None, upgrade: bool = None):
        """Create a new Application object.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            name (str):  Name of the application
            key (str):  Key to identify the application
            type (str):  Type of the application
            availability (str):  Application access level for tenants
            context_path (str):  The path where the application is accessible
            manifest (dict):  Microservice or web application manifest
            roles (str):  List of roles provided by the application
            required_roles (str):  List of roles required by the application
            breadcrumbs (bool):  Whether the (web) application uses breadcrumbs
            content_security_policy (str):  The content security policy of the application
            dynamic_options_url (str):  A URL to a JSON object with dynamic content options
            global_title (str):  The global title of the application
            legacy (bool):  Whether the (web) application is of legacy type
            right_drawer (bool): Whether the (web) application uses the
                right hand context menu
            upgrade (bool):  Whether the (web) application uses both Angular and AngularJS
        """
        super().__init__(c8y=c8y)
        self._u_name = name
        self._u_type = type
        self._u_key = key
        self.owner = None
        self._u_availability = availability
        self._u_contextPath = context_path
        self.manifest = manifest
        self._u_roles = roles
        self._u_required_roles = required_roles
        self._u_breadcrumbs = breadcrumbs
        self.__u_content_security_policy = content_security_policy
        self._u_dynamic_options_url = dynamic_options_url
        self.__u_global_title = global_title
        self._u_legacy = legacy
        self._u_rightDrawer = right_drawer
        self._u_upgrade = upgrade

    name = SimpleObject.UpdatableProperty('_u_name')
    type = SimpleObject.UpdatableProperty('_u_type')
    key = SimpleObject.UpdatableProperty('_u_key')
    availability = SimpleObject.UpdatableProperty('_u_availability')
    context_path = SimpleObject.UpdatableProperty('_u_contextPath')
    roles = SimpleObject.UpdatableProperty('_u_roles')
    required_roles = SimpleObject.UpdatableProperty('_u_required_roles')
    breadcrumbs = SimpleObject.UpdatableProperty('_u_breadcrumbs')
    content_security_policy = SimpleObject.UpdatableProperty('__u_content_security_policy')
    dynamic_options_url = SimpleObject.UpdatableProperty('_u_dynamic_options_url')
    global_title = SimpleObject.UpdatableProperty('__u_global_title')
    legacy = SimpleObject.UpdatableProperty('_u_legacy')
    right_drawer = SimpleObject.UpdatableProperty('_u_rightDrawer')
    upgrade = SimpleObject.UpdatableProperty('_u_upgrade')

    @classmethod
    def from_json(cls, json: dict) -> Application:
        # (no doc update required)
        obj = super()._from_json(json, Application())
        obj.owner = json['owner']['tenant']['id']
        return obj

    def create(self) -> Application:
        """Create the Application within the database.

        Returns:
            A fresh Application object representing what was
            created within the database (including the ID).
        """
        return super()._create()

    def update(self) -> Application:
        """Update the Application within the database.

        Note: This will only send changed fields to increase performance.

        Returns:
            A fresh Application object representing what the updated
            state within the database (including the ID).
        """
        return super()._update()

    def delete(self):
        """Delete the Application within the database."""
        super()._delete()


class Applications(CumulocityResource):
    """Provides access to the Application API.

    This class can be used for get, search for, create, update and
    delete applications within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Application-API
    """

    def __init__(self, c8y: CumulocityRestApi):
        super().__init__(c8y=c8y, resource='application/applications')

    def get(self, application_id: str) -> Application:
        """Retrieve a specific object from the database.

        Args:
            application_id (str):  The database ID of the application

        Returns:
            An Application instance representing the object in the database.
        """
        return Application.from_json(self._get_object(application_id))

    def select(self, name: str = None, type: str = None, owner: str = None, user: str = None,
               tenant: str = None, subscriber: str = None, provided_for: str = None,
               limit: int = None, page_size: int = 100) -> Generator[Application]:
        """Query the database for applications and iterate over the results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters' specification. Filters can be
        combined (within reason).

        Args:
            name (str):  Name of an application (no wildcards allowed)
            type (str):  Application type (e.g. HOSTED)
            owner (str):  ID of a Cumulocity user which owns the application
            user (str):  ID of a Cumulocity user which has general access
            tenant (str):  ID of a Cumulocity tenant which either owns the
                application or is subscribed to it
            subscriber (str):  ID of a Cumulocity tenant which is subscribed
                to the application (and may own it)
            provided_for (str):  ID of a Cumulocity tenant which is subscribed
                to the application but does not own it
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of events which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            A Generator for Application objects.
        """
        base_query = self._build_base_query(name=name, type=type, owner=owner, tenant=tenant,
                                            user=user, subscriber=subscriber, providedFor=provided_for,
                                            page_size=page_size)
        return super()._iterate(base_query, limit, Application.from_json)

    def get_all(self, name: str = None, type: str = None, owner: str = None, user: str = None,
                tenant: str = None, subscriber: str = None, provided_for: str = None,
                limit: int = None, page_size: int = 100) -> List[Application]:
        """Query the database for applications and return the results as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        See `select` for a documentation of arguments.

        Returns:
            List of Application objects
        """
        return list(self.select(name=name, type=type, owner=owner, user=user,
                                tenant=tenant, subscriber=subscriber, provided_for=provided_for,
                                limit=limit, page_size=page_size))

    def upload_attachment(self, application_id: str, file: str | BinaryIO):
        """Upload application binary for a registered application.

        Args:
            application_id (str):  The Cumulocity object ID of the application
            file (str|BinaryIO):  File path or file-like object to upload.

         See also: https://cumulocity.com/api/#tag/Application-binaries
         """
        self.c8y.post_file(self.build_object_path(application_id) + '/binaries', file=file)
