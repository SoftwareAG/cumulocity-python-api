# Copyright (c) 2020 Software AG,
# Darmstadt, Germany and/or Software AG USA Inc., Reston, VA, USA,
# and/or its subsidiaries and/or its affiliates and/or their licensors.
# Use, reproduction, transfer, publication or disclosure is prohibited except
# as specifically provided for in your License Agreement with Software AG.

class SimpleObjectParser(object):
    """A parser for simple (without fragments) Cumulocity database objects.

    The parser converts between an object and a JSON representation using
    a simple field mapping dictionary.
    """

    def __init__(self, mapping):
        self._obj_to_json = {**mapping, 'id': 'id'}
        self._json_to_object = {v: k for k, v in self._obj_to_json.items()}

    def from_json(self, obj_json, new_obj, skip=None):
        """Update a given object instance with data from a JSON object.

        This function uses the parser's mapping definition, only fields
        are parsed that are part if this.

        Use the skip list to skip certain objects fields within the update
        regardless whether they are defined in the mapping.

        Params:
            obj_json: JSON object (nested dict) to parse
            new_obj:  object instance to update (usually newly created)
            skip:  list of object field names to skip or None if nothing
                should be skipped

        Returns:
            The updated object instance.
        """
        for json_key, field_name in self._json_to_object.items():
            if not skip or field_name not in skip:
                if json_key in obj_json:
                    new_obj.__dict__[field_name] = obj_json[json_key]
        return new_obj

    def to_json(self, obj: object, include=None, exclude=None):
        """Build a JSON representation of an object.

        Use the include list to limit the represented fields to a specific
        subset (e.g. just the updated fields). Use the exclude list to ignore
        certain fields in the representation.

        If a field is present in both lists, it will be excluded.

        Params:
            include:  an iterable of object fields to include or None if all
                fields should be included
            exclude:  an iterable of object fields to exclude or None of no
                field should be included

        Returns:
            A JSON representation (nested dict) of the object.
        """
        obj_json = {}
        for name, value in obj.__dict__.items():
            if include is None or name in include:  # field is included
                if exclude is None or name not in exclude:  # field is not included
                    if value is not None and name in self._obj_to_json:
                        obj_json[self._obj_to_json[name]] = value
        return obj_json

    def to_full_json(self, obj, ignore_list=None):
        repr_key = '+full_json+'+str(ignore_list)+'+'
        if not ignore_list:
            ignore_list = []
        if repr_key not in obj.__dict__:
            obj_json = {}
            for name, value in obj.__dict__.items():
                if name not in ignore_list:
                    if value and name in self._obj_to_json:
                        obj_json[self._obj_to_json[name]] = value
            obj.__dict__[repr_key] = obj_json
        return obj.__dict__[repr_key]

    def to_diff_json(self, obj):
        """Convert a database object to a JSON representation considering only updated fields.

        Updated fields need to be signaled via the _signal_updated_field method. The signaled
        name is extracted from the object fields. For this to function the field name needs to
        be identical to the signaled name.

        The formatted JSON string is stored within the object reference for performance reasons.
        """
        if '+diff_json+' not in obj.__dict__:
            obj_json = {}
            if obj._updated_fields:
                for name in obj._updated_fields:
                    obj_json[self._obj_to_json[name]] = obj.__dict__[name]
            obj.__dict__['+diff_json+'] = obj_json
        return obj.__dict__['+diff_json+']


class ComplexObjectParser(SimpleObjectParser):
    """A parser for complex (with fragments) Cumulocity database objects.

    The parser converts between an object and a JSON representation using
    a simple field mapping dictionary. All other fields are mapped as
    fragments, an exclusive list can be given to skip unwanted fields.
    """

    def __init__(self, to_json_mapping, no_fragments_list):
        super().__init__(to_json_mapping)
        self.__ignore_set = {*no_fragments_list, *to_json_mapping.values(), 'self', 'id'}

    def from_json(self, obj_json, new_obj, skip=None):
        new_obj = super().from_json(obj_json, new_obj)
        new_obj.fragments = self.__parse_fragments(obj_json)
        return new_obj

    def to_json(self, obj, include=None, exclude=None):
        obj_json = super().to_json(obj, include, exclude)
        obj_json.update(self.__format_fragments(obj))
        return obj_json

    def to_full_json(self, obj, ignore_list=None):
        obj_json = super().to_json(obj, exclude=self.__ignore_set)
        obj_json.update(self.__format_fragments(obj))
        return obj_json

    def to_diff_json(self, obj):
        obj_json = super().to_diff_json(obj)
        obj_json.update(self.__format_updated_fragments(obj))
        return obj_json

    def __parse_fragments(self, obj_json):
        return {name: body for name, body in obj_json.items() if name not in self.__ignore_set}

    @staticmethod
    def __format_fragments(obj):
        return dict(obj.__dict__['fragments'].items())

    @staticmethod
    def __format_updated_fragments(obj):
        if not obj._updated_fragments:
            return {}
        return {name: fragment for name, fragment in obj.fragments.items() if name in obj._updated_fragments}
