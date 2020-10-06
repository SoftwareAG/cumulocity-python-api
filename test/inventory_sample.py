from c8y_app import CumulocityApi
from c8y_model import ManagedObject, Fragment

c8y = CumulocityApi()

mo1 = ManagedObject(name='test')
mo1.add_attribute(name='c8y_attribute', value="some message string")
mo1.add_fragment(name='c8y_Fragment', region='EMEA')
mo1.add_fragments([Fragment('c8y_F1', v=1), Fragment('c8y_F2', v=2)])
mo1.c8y = c8y  # needs to be defined for object-oriented database access
mo1.create()
mo1.create()

mo_chg = ManagedObject()
mo_chg.c8y = c8y  # this is needed to invoke db access methods directly on object
mo_chg.add_fragment('c8y_F3', v=3)
mo_chg.owner = 'None'
print(mo_chg.get_updates())

for mo in c8y.inventory.select(fragment='c8y_Fragment'):
    print('Adding fragment to object ' + mo.id)
    mo_chg.update(mo.id)

for mo in c8y.inventory.select(fragment='c8y_Fragment'):
    print('Fragments of object ' + mo.id + ': ' + str(mo.fragments.keys()))
    print(f'Value of c8y_Fragment.region: {mo.c8y_Fragment.region}')
    print(f'Value of c8y_attribute: {mo.c8y_attribute}')
    mo.delete()
