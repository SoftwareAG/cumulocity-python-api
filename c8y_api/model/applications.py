# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model._base import _DatabaseObject, CumulocityResource
from c8y_api.model._parser import SimpleObjectParser


class Application(_DatabaseObject):

    __parser = SimpleObjectParser({
        'id': 'id',
        'name': 'name',
        'type': 'type',
        'availability': 'availability'})

    def __init__(self, c8y=None, name=None, type=None, availability=None, owner=None):  # noqa (type)
        super().__init__(c8y=c8y)
        self.name = name
        self.type = type
        self.availability = availability
        self.owner = owner

    @classmethod
    def from_json(cls, application_json):
        application = Application(name=application_json['name'],
                                  type=application_json['type'],
                                  availability=application_json['availability'],
                                  owner=application_json['owner']['tenant']['id'])
        application.id = application_json['id']
        return application


class Applications(CumulocityResource):

    def __init__(self, c8y):
        super().__init__(c8y=c8y, resource='application/applications')

    def get(self, application_id):
        return Application.from_json(self._get_object(application_id))

    def select(self, name=None, tenant=None, owner=None, user=None, page_size=100):
        """ Select applications by various discriminators.

        This is a lazy implementation; results are fetched in pages but
        parsed and returned one by one. The search discriminators are
        mutually exclusive, hence only one can be used at a time.

        :param name:  select applications by their name
        :param tenant:  select applications by subscribing tenant
        :param owner:  select applications by owning tenant
        :param user:  select applications by subscribed user
        :param page_size:  number of objects to fetch per request
        :return:  Generator of Application instances
        """
        # 1_ define base query (excl. page number)
        if name:
            base_query = '/application/applicationsByName/' + name
        elif tenant:
            base_query = '/application/applicationsByTenant/' + tenant
        elif owner:
            base_query = '/application/applicationsByOwner/' + owner
        elif user:
            base_query = '/application/applicationsByUser/' + user
        else:
            base_query = '/application/applications'
        base_query = base_query + '?pageSize=' + str(page_size) + '&currentPage='

        # 2_ iterate over pages
        page_number = 1
        while True:
            results = [Application.from_json(x) for x in self._get_page(base_query, page_number)]
            if not results:
                break
            for result in results:
                result.c8y = self.c8y  # inject c8y connection into instance
                yield result
            page_number = page_number + 1

    def get_all(self, name=None, tenant=None, owner=None, user=None, page_size=100):
        """ Select applications by various discriminators.

        In contract to the select method this version is not lazy. It will
        collect the entire result set before returning. The search
        discriminators are mutually exclusive, hence only one can be used
        at a time.

        :param name:  select applications by their name
        :param tenant:  select applications by subscribing tenant
        :param owner:  select applications by owning tenant
        :param user:  select applications by subscribed user
        :param page_size:  number of objects to fetch per request
        :return:  Generator of Application instances
        """
        return list(self.select(name=name, tenant=tenant, owner=owner, user=user, page_size=page_size))
