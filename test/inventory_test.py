import uuid
import pytest

from c8y_api.app import CumulocityApi
from c8y_api.model import ManagedObject

c8y = CumulocityApi()


def generate_uuid():
    return str(uuid.uuid1())


@pytest.fixture
def num():
    return 3


@pytest.fixture
def random_name():
    return generate_uuid()


@pytest.fixture
def new_object_from_type(random_name):
    return ManagedObject(type=random_name, name=random_name)


@pytest.fixture
def new_object_from_fragment(random_name):
    return ManagedObject(name=random_name).add_fragment(random_name, key='value')


@pytest.fixture
def new_objects_from_type(random_name, num):
    return [ManagedObject(type=random_name, name=f'{random_name}_{i}') for i in range(1, num+1)]


@pytest.fixture
def new_objects_from_fragment(random_name, num):
    mos = [ManagedObject(name=f'{random_name}_{i}') for i in range(1, num+1)]
    for mo in mos:
        mo.add_fragment(random_name, key='value')
    return mos


@pytest.fixture
def db_object_from_type(new_object_from_type):
    mo = new_object_from_type
    mo.c8y = c8y
    mo.create()
    mos = c8y.inventory.get_all(mo.type)
    print(f"Created ManagedObject #{mos[0].id}, type {mo.type}.")
    yield mos[0]
    mos[0].delete()
    print(f"Deleted ManagedObject #{mos[0].id}, type {mo.type}.")


@pytest.fixture
def db_objects_from_type(new_objects_from_type):
    mos = new_objects_from_type
    type_name = mos[0].type
    c8y.inventory.create(*mos)
    mos2 = c8y.inventory.get_all(type=type_name)
    ids = [mo.id for mo in mos2]
    print(f"Created ManagedObjects {ids}, type {type_name}")
    yield mos2
    c8y.inventory.delete(*[mo.id for mo in mos2])
    print(f"Deleted ManagedObjects {ids}, type {type_name}")


@pytest.fixture
def db_objects_from_fragment(new_objects_from_fragment):
    mos = new_objects_from_fragment
    fragment_name = next(iter(mos[0].fragments.keys()))
    c8y.inventory.create(*mos)
    mos2 = c8y.inventory.get_all(fragment=fragment_name)
    ids = [mo.id for mo in mos2]
    print(f"Created ManagedObjects {ids}, fragment {fragment_name}")
    yield mos2
    c8y.inventory.delete(*[mo.id for mo in mos2])
    print(f"Deleted ManagedObjects {ids}, type {fragment_name}")


def test_create_and_delete_multiple(new_objects_from_type):
    mos = new_objects_from_type
    c8y.inventory.create(*mos)
    print(f"Created {len(mos)} ManagedObject instances with type {mos[0].type}.")
    mos2 = c8y.inventory.get_all(type=mos[0].type)
    assert len(mos2) == len(mos)
    c8y.inventory.delete(*[mo.id for mo in mos2])
    mos3 = c8y.inventory.get_all(type=mos[0].type)
    print(f"All ManagedObject instances removed.")
    assert not mos3


def test_get_object_by_id(db_object_from_type):
    oid = db_object_from_type.id
    mo = c8y.inventory.get(oid)
    assert mo.type == db_object_from_type.type
    assert mo.id
    assert mo.owner
    assert not mo.fragments
    assert mo.update_time
    assert mo.creation_time


def test_select_by_type(db_objects_from_type):
    mos = db_objects_from_type
    mos2 = [x for x in c8y.inventory.select(type=mos[0].type)]
    mos3 = [x for x in c8y.inventory.select(type=generate_uuid())]
    assert len(mos2) == len(mos)
    assert len(mos3) == 0


def test_select_by_fragment(db_objects_from_fragment):
    mos = db_objects_from_fragment
    fragment_name = next(iter(mos[0].fragments.keys()))
    mos2 = [x for x in c8y.inventory.select(fragment=fragment_name)]
    mos3 = [x for x in c8y.inventory.select(fragment=generate_uuid())]
    assert len(mos2) == len(mos)
    assert len(mos3) == 0


def test_update_type(db_object_from_type):
    oid = db_object_from_type.id
    mo = c8y.inventory.get(oid)
    mo.type = 'NewType'
    mo.update()
    mo2 = c8y.inventory.get(oid)
    assert mo2.type == 'NewType'


def test_add_fragment(db_object_from_type):
    oid = db_object_from_type.id
    mo1 = c8y.inventory.get(oid)
    mo1.add_fragment("AddedFragment", foo='foo-value', bar='bar-value')
    mo1.update()
    mo2 = c8y.inventory.get(oid)
    assert mo2.AddedFragment
    assert mo2.AddedFragment.foo == 'foo-value'
    assert mo2.AddedFragment.bar == 'bar-value'


def test_update_multiple(db_objects_from_type):
    ids = [mo.id for mo in db_objects_from_type]
    update_mo = ManagedObject()
    update_mo.type = generate_uuid()
    update_mo.add_fragment('NewFragment', key='value')
    c8y.inventory.update(update_mo, *ids)

    mos = c8y.inventory.get_all(type=update_mo.type)
    assert len(mos) == len(ids)
    for mo in mos:
        assert mo.type == update_mo.type
        assert mo.NewFragment.key == 'value'


def test_fail_update_multiple_with_id():
    update_mo = ManagedObject()
    update_mo.id = 'anything'
    with pytest.raises(ValueError) as err:
        c8y.inventory.update(update_mo, 'foo', 'bar')
    assert 'ID' in str(err.value)
