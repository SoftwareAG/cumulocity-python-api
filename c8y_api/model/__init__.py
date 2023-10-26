# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

from c8y_api.model.administration import *
from c8y_api.model.alarms import *
from c8y_api.model.applications import *
from c8y_api.model.audit import *
from c8y_api.model.binaries import *
from c8y_api.model.events import *
from c8y_api.model.identity import *
from c8y_api.model.inventory import *
from c8y_api.model.managedobjects import *
from c8y_api.model.measurements import *
from c8y_api.model.notification2 import *
from c8y_api.model.operations import *
from c8y_api.model.tenant_options import *


__all__ = [
    # API Classes
    'Inventory',
    'DeviceInventory',
    'DeviceGroupInventory',
    'Binaries',
    'Identity',
    'Measurements',
    'Events',
    'Alarms',
    'Subscriptions',
    'Users',
    'GlobalRoles',
    'Operations',
    'BulkOperations',
    'Applications',
    'TenantOptions',
    'AuditRecords',
    # Model Classes
    'CumulocityResource',
    'ManagedObject',
    'Device',
    'DeviceGroup',
    'ExternalId',
    'Binary',
    'Measurement',
    'Event',
    'Alarm',
    'Series',
    'Subscription',
    'Tokens',
    'Availability',
    'Fragment',
    'NamedObject',
    'User',
    'GlobalRole',
    'Permission',
    'ReadPermission',
    'WritePermission',
    'AnyPermission',
    'Operation',
    'BulkOperation',
    'Application',
    'TenantOption',
    'AuditRecord',
    # Measurement Helpers
    'Units',
    'Celsius',
    'Centimeters',
    'Count',
    'CubicMeters',
    'Grams',
    'Kelvin',
    'Kilograms',
    'Liters',
    'Meters',
    'Percentage',
    'Value',
]
