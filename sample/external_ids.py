from c8y_api.app import CumulocityApi
from c8y_api.model import ExternalId, ManagedObject

# When using the App version, the API handle is initialized using
# standard environment variables
c8y = CumulocityApi()

# 1_ create a random managed object we can link to
name = 'TestObject-148'
mo = ManagedObject(c8y, type='TestObject', name=name)
mo.create()
mo_id = c8y.inventory.get_all(name=name)[0].id

# 2_ create an external ID linking to the object
# This can be done in two different ways; below are both, using
# different ID types to allow the same ID multiple times.
external_id = 'id-' + name

# Option A: Using Identiy API
c8y.identity.create(external_id, 'type_option_a', mo_id)

# Option B: Using ExternalId
eid = ExternalId(c8y, external_id, 'type_option_b', mo_id)
eid.create()

# 3_ pull the linked managed object
# Again, we have two ways to do this, corresponding to the above
mo1 = c8y.identity.get_object(external_id, 'type_option_a')
mo2 = eid.get_object()
assert mo1.id == mo2.id

# 4_ remove the external ID
c8y.identity.delete(external_id, 'type_option_a')
eid.delete()

# 5_ clean up the managed
mo1.delete()
