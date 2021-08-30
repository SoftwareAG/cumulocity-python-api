# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api._base_api import CumulocityRestApi

from c8y_api.model.inventory import Inventory, Identity, Binaries, DeviceGroupInventory, DeviceInventory
from c8y_api.model.administration import Users, GlobalRoles, InventoryRoles
from c8y_api.model.measurements import Measurements
from c8y_api.model.applications import Applications
from c8y_api.model.events import Events
from c8y_api.model.alarms import Alarms


class CumulocityApi(CumulocityRestApi):

    def __init__(self, base_url, tenant_id, username, password, tfa_token=None, application_key=None):
        super().__init__(base_url, tenant_id, username, password, tfa_token, application_key)
        self.__measurements = Measurements(self)
        self.__inventory = Inventory(self)
        self.__binaries = Binaries(self)
        self.__group_inventory = DeviceGroupInventory(self)
        self.__device_inventory = DeviceInventory(self)
        self.__identity = Identity(self)
        self.__users = Users(self)
        self.__global_roles = GlobalRoles(self)
        self.__inventory_roles = InventoryRoles(self)
        self.__applications = Applications(self)
        self.__events = Events(self)
        self.__alarms = Alarms(self)

    @property
    def measurements(self):
        return self.__measurements

    @property
    def inventory(self):
        return self.__inventory

    @property
    def binaries(self):
        return self.__binaries

    @property
    def group_inventory(self):
        return self.__group_inventory

    @property
    def device_inventory(self):
        return self.__device_inventory

    @property
    def identity(self):
        return self.__identity

    @property
    def users(self):
        return self.__users

    @property
    def global_roles(self):
        return self.__global_roles

    @property
    def inventory_roles(self):
        return self.__inventory_roles

    @property
    def applications(self):
        return self.__applications

    @property
    def events(self):
        return self.__events

    @property
    def alarms(self):
        return self.__alarms
