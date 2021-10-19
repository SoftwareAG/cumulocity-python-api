# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

from typing import Generator, List

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
        'name': 'name',
        'type': 'type',
        'availability': 'availability'})
    _resource = 'application/applications'

    EXTERNAL_TYPE = "EXTERNAL"
    HOSTED_TYPE = "HOSTED"
    MICROSERVICE_TYPE = "MICROSERVICE"

    def __init__(self, c8y: CumulocityRestApi = None, name: str = None, type: str = None, availability: str = None,
                 owner: str = None):
        super().__init__(c8y=c8y)
        self.name = name
        self.type = type
        self.availability = availability
        self.owner = owner

    @classmethod
    def from_json(cls, json: dict) -> Application:
        # (no doc update required)
        obj = super()._from_json(json, Application())
        obj.owner = json['owner']['tenant']['id']
        return obj


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
        to objects which meet the filters specification.  Filters can be
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
