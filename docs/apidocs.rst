.. Copyright (c) 2020 Software AG,
   Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
   and/or its subsidiaries and/or its affiliates and/or their licensors.
   Use, reproduction, transfer, publication or disclosure is prohibited except
   as specifically provided for in your License Agreement with Software AG.

API Documentation
=====================

REST API Connector
------------------

.. automodule::  c8y_api
    :members: CumulocityRestApi, CumulocityApi, CumulocityDeviceRegistry
    :special-members: __init__


Application Helpers
-------------------

.. automodule::  c8y_api.app
    :members: SimpleCumulocityApp, MultiTenantCumulocityApp
    :inherited-members:
    :special-members: __init__


Main API Classes
----------------

.. automodule:: c8y_api.model
    :members: Inventory, DeviceInventory, Identity, Binaries, Measurements, Events, Alarms, Users, GlobalRoles, InventoryRoles, Subscriptions, Tokens, Operations, BulkOperations, Applications, TenantOptions, AuditRecords


Object Models
-------------

.. automodule:: c8y_api.model
    :members: ManagedObject, Device, DeviceGroup, ExternalId, Binary, Measurement, Event, Alarm, Series, Subscription, Tokens, Availability, Fragment, NamedObject, User, GlobalRole, Permission, ReadPermission, WritePermission, AnyPermission, Operation, BulkOperation, Application, TenantOption, AuditRecord
    :special-members: __init__

Object Model Additions
----------------------

.. automodule:: c8y_api.model
    :members: Units, Celsius, Centimeters, Count, CubicMeters, Grams, Kelvin, Kilograms, Liters, Meters, Percentage, Value
    :undoc-members:
