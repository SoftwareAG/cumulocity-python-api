class _DictWrapper(object):

    def __init__(self, dictionary, on_update=None):
        self.__dict__['items'] = dictionary
        self.__dict__['on_update'] = on_update

    def has(self, name):
        return name in self.items

    def __getattr__(self, name):
        item = self.items[name]
        return item if not isinstance(item, dict) else _DictWrapper(item, self.on_update)

    def __setattr__(self, name, value):
        if self.on_update:
            self.on_update()
        self.items[name] = value

    def __str__(self):
        return self.__dict__['items'].__str__()


class _UpdatableProperty(object):

    def __init__(self, name=None):
        self.name = name

    def __get__(self, obj, _):
        return obj.__dict__[self.name]

    def __set__(self, obj, value):
        obj._signal_updated_field(self.name)
        obj.__dict__[self.name] = value

    def __delete__(self, obj):
        obj._signal_updated_field(self.name)
        obj.__dict__[self.name] = None


class _NotUpdatableProperty(object):

    def __init__(self, prop_name, orig_name):
        self.prop_name = prop_name
        self.orig_name = orig_name

    def __get__(self, obj, _):
        return obj.__dict__[self.prop_name]

    def __set__(self, obj, value):
        raise TypeError(f"Attribute '{self.orig_name}' is read-only.")

    def __delete__(self, obj):
        raise TypeError(f"Attribute '{self.orig_name}' is read-only.")


class _UpdatableThingProperty(object):

    def __init__(self, prop_name, orig_name):
        self.prop_name = prop_name
        self.orig_name = orig_name
        self._updatable = None

    def __get__(self, obj, _):
        print('get ' + self.prop_name)
        if not self._updatable:
            def on_update(n1, n2):
                if not obj.__dict__[n1]:  # has not been preserved
                    obj.__dict__[n2] = copy(obj.__dict__[n1])
            self._updatable = _UpdatableThing(obj.__dict__[self.prop_name],
                                              lambda: on_update(self.prop_name, self.orig_name))
        return self._updatable

    def __set__(self, obj, value):
        if not obj.__dict__[self.orig_name]:  # has not been preserved
            obj.__dict__[self.orig_name] = copy(obj.__dict__[self.prop_name])
        obj.__dict__[self.prop_name] = value

    @staticmethod
    def _preserve_original_set(obj, name, orig_name):
        if not obj.__dict__[orig_name]:
            obj.__dict__[orig_name] = set(obj.__dict__[name])


class _UpdatableSetProperty(object):

    def __init__(self, prop_name, orig_name):
        self.prop_name = prop_name
        self.orig_name = orig_name

    def __get__(self, obj, _):
        self._preserve_original(obj)
        return obj.__dict__[self.prop_name]

    def __set__(self, obj, value):
        assert isinstance(value, set)
        self._preserve_original(obj)
        obj.__dict__[self.prop_name] = value

    def __delete__(self, obj):
        self._preserve_original(obj)
        obj.__dict__[self.prop_name] = None

    def _preserve_original(self, obj):
        if not obj.__dict__[self.orig_name]:
            obj.__dict__[self.orig_name] = set(obj.__dict__[self.prop_name])


class _UpdatableSet(set):

    def __init__(self, data=None):
        super().__init__(data)
        self.is_updated = False

    def __getattribute__(self, name):
        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):  # it's a function
            def func(*args, **kwargs):
                return attr(*args, **kwargs)
            self.is_updated = True
            return func
        return attr


class _UpdatableThing:

    def __init__(self, thing, on_access):
        self.on_access = on_access
        self.thing = thing

    def __getattribute__(self, name):
        print('getattr ' + name)
        attr = object.__getattribute__(object.__getattribute__(self, 'thing'), name)
        if hasattr(attr, '__call__'):  # it's a function
            def func(*args, **kwargs):
                return attr(*args, **kwargs)
            object.__getattribute__(self, 'on_access')()
            return func
        return attr


