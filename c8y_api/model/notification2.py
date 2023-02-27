# Copyright (c) 2021 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from __future__ import annotations

import json as js
from typing import List, Set, Generator
import urllib.parse
import uuid

from c8y_api._base_api import CumulocityRestApi
from c8y_api.model._base import SimpleObject, CumulocityResource
from c8y_api.model._parser import SimpleObjectParser


class Subscription(SimpleObject):
    """ Represent a Notification 2.0 subscription within the database.

    Instances of this class are returned by functions of the corresponding
    Subscriptions API. Use this class to create new options.

    See also: https://cumulocity.com/api/#tag/Subscriptions
    """

    class Context(object):
        """Notification context types."""
        MANAGED_OBJECT = 'mo'
        TENANT = 'tenant'

    class ApiFilter(object):
        """Notification API filter types."""
        ANY = '*'
        ALARMS = 'alarms'
        ALARMS_WITH_CHILDREN = 'alarmsWithChildren'
        EVENTS = 'events'
        EVENTS_WITH_CHILDREN = 'eventsWithChildren'
        MANAGED_OBJECTS = 'managedobjects'
        MEASUREMENTS = 'measurements'
        OPERATIONS = 'operations'

    _resource = '/notification2/subscriptions'
    _parser = SimpleObjectParser({
            'name': 'subscription',
            'context': 'context',
            'fragments': 'fragmentsToCopy'})
    _accept = 'application/vnd.com.nsn.cumulocity.subscription+json'

    def __init__(self, c8y: CumulocityRestApi = None, name: str = None, context: str = None, source_id: str = None,
                 api_filter: List[str] = None, type_filter: str = None,
                 fragments: List[str] = None):
        """ Create a new Subscription instance.

        Args:
            c8y (CumulocityRestApi):  Cumulocity connection reference; needs
                to be set for direct manipulation (create, delete)
            name (str):  Subscription name
            context (str):  Subscription context.
            source_id (str):  Managed object ID the subscription is for.
            api_filter (List[str]):  List of APIs/resources to subscribe for.
            type_filter (str):  Object type the subscription is for.

        Returns:
            Subscription instance
        """
        super().__init__(c8y)
        self.name = name
        self.context = context
        self.source_id = source_id
        self.api_filter = api_filter
        self.type_filter = type_filter
        self.fragments = fragments

    def _to_json(self, only_updated=False, exclude: Set[str] = None) -> dict:
        json = super()._to_json(only_updated=only_updated, exclude=exclude)
        if self.source_id:
            json['source'] = {'id': self.source_id}
        if self.api_filter or self.type_filter:
            subscription_filter = {'apis': self.api_filter if self.api_filter else None,
                                   'typeFilter': self.type_filter if self.type_filter else None}
            json['subscriptionFilter'] = subscription_filter
        return json

    @classmethod
    def from_json(cls, json: dict) -> Subscription:
        """Create a Subscription instance from Cumulocity JSON format.

        Caveat: this function is primarily for internal use and does not
        return a full representation of the JSON. It is used for object
        creation and update within Cumulocity.

        Params:
            json (dict): The JSON to parse.

        Returns:
            A Subscription instance.
        """
        subscription = super()._from_json(json, Subscription())
        subscription.source_id = json['source']['id']
        if 'subscriptionFilter' in json:
            if 'apis' in json['subscriptionFilter']:
                subscription.api_filter = json['subscriptionFilter']['apis']
            if 'typeFilter' in json['subscriptionFilter']:
                subscription.type_filter = json['subscriptionFilter']['typeFilter']
        return subscription

    def create(self) -> Subscription:
        """ Create a new subscription within the database.

        Returns:
            A fresh Subscription instance representing the created
            subscription within the database.

        See also function Subscriptions.create which doesn't parse the result.
        """
        return self._create()


class Subscriptions(CumulocityResource):
    """Provides access to the Notification 2.0 Subscriptions API.

    This class can be used for get, search for, create, and
    delete Notification2 subscriptions within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Subscriptions
              https://cumulocity.com/guides/reference/notifications/
    """

    def __init__(self, c8y: CumulocityRestApi):
        super().__init__(c8y, '/notification2/subscriptions')

    def get(self, subscription_id: str) -> Subscription:
        """ Retrieve a specific subscription from the database.

        Args:
            subscription_id (str):  Subscription ID

        Returns:
             A Subscription instance

        Raises:
            KeyError if the given ID is not defined within the database
        """
        subscription = Subscription.from_json(super()._get_object(subscription_id))
        subscription.c8y = self.c8y  # inject c8y connection into instance
        return subscription

    def select(self, context: str = None, source: str = None,
               limit: int = None, page_size: int = 1000) -> Generator[Subscription]:
        """ Query the database for subscriptions and iterate over the
        results.

        This function is implemented in a lazy fashion - results will only be
        fetched from the database as long there is a consumer for them.

        All parameters are considered to be filters, limiting the result set
        to objects which meet the filters' specification.  Filters can be
        combined (within reason).

        Args:
            context (str):  Subscription context.
            source (str):  Managed object ID the subscription is for.
            limit (int): Limit the number of results to this number.
            page_size (int): Define the number of objects which are read (and
                parsed in one chunk). This is a performance related setting.

        Returns:
            Generator for Subscription instances
        """
        base_query = self._build_base_query(context=context, source=source, page_size=page_size)
        return super()._iterate(base_query, limit, Subscription.from_json)

    def get_all(self, context: str = None, source: str = None,
                limit: int = None, page_size: int = 1000) -> List[Subscription]:
        """ Query the database for subscriptions and return the results
        as list.

        This function is a greedy version of the `select` function. All
        available results are read immediately and returned as list.

        Returns:
            List of Subscription instances.
        """
        return list(self.select(context=context, source=source, limit=limit, page_size=page_size))

    def create(self, *subscriptions: Subscription) -> None:
        """ Create subscriptions within the database.

        Args:
            subscriptions (*TenantOption):  Collection of Subscription instances
        """
        super()._create(Subscription.to_full_json, *subscriptions)

    def delete_by(self, context: str = None, source: str = None) -> None:
        """ Delete subscriptions within the database.

        Args:
            context (str):  Subscription context
            source (str):  Managed object ID the subscription is for.
        """
        base_query = self._build_base_query(context=context, source=source)
        # remove &page_number= from the end
        query = base_query[:base_query.rindex('&')]
        self.c8y.delete(query)


class Tokens(CumulocityResource):
    """Provides access to the Notification 2.0 token generation API.

    This class can be used for get, search for, create, and
    delete Notification2 subscriptions within the Cumulocity database.

    See also: https://cumulocity.com/api/#tag/Tokens
              https://cumulocity.com/guides/reference/notifications/
    """

    _subscriber_uuid = uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/SoftwareAG/cumulocity-python-api')
    _default_subscriber = 'c8yapi' + str(_subscriber_uuid).replace('-', '')

    def __init__(self, c8y: CumulocityRestApi):
        super().__init__(c8y, '/notification2')
        self.host = urllib.parse.urlparse(c8y.base_url).netloc

    def generate(self, subscription: str, expires: int = 60, subscriber: str = None) -> str:
        """Generate a new access token.

        Args:
            subscription (str): Subscription name
            expires (int):  Expiration time in minutes
            subscriber (str):  Subscriber Id (name)

        Returns:
            JWT access token as string.
        """
        td_json = self._build_token_definition(subscription, expires, subscriber)
        token_json = self.c8y.post(self.resource + '/token', td_json)
        return token_json['token']

    def renew(self, token: str):
        """Renew a token."""

    def unsubscribe(self, token: str):
        """Invalidate a token and unsubscribe a subscriber.

        Args:
            token (str):  Subscribed token
        """
        result_json = self.c8y.post(self.resource + '/unsubscribe?token=' + token, json={})
        if not result_json['result'] == 'DONE':
            raise RuntimeError(f"Unexpected response: {js.dumps(result_json)}")

    def build_websocket_uri(self, token: str):
        """Build websocket access URL.

        Args:
            token (str):  Subscriber access token

        Returns:
             A websocket (wss://) URL to access the subscriber channel.
        """
        return f'wss://{self.host}/notification2/consumer/?token={token}'

    def _build_token_definition(self, subscription: str, expires: int, subscriber: str = None):
        return {
            'subscriber': subscriber or self._default_subscriber,
            'subscription' : subscription,
            'expiresInMinutes' : expires
        }
