from collections import namedtuple

from .exc import NotUnique


def generate_objects(artifacts, kwargs):
    '''generate_objects takes a list of artifacts that are supported by
    a create function and compares it to the kwargs passed in to the create
    function. If a kwarg is found that is not in the artifacts list a RuntimeError
    is raised.
    '''
    for k in kwargs.keys():
        if k not in artifacts:
            raise RuntimeError('{} is not a valid argument'.format(k))
    return namedtuple("Objects", ",".join(artifacts))


def generate_role_objects(objects):
    '''generate_role_objects assembles a dictionary of all possible objects by name.
    It will raise an exception if any of the objects share a name due to the fact that
    it is to be used with apply_roles, which expects unique object names.

    roles share a common name e.g. admin_role, member_role. This ensures that the
    roles short hand used for mapping Roles and Users in apply_roles will function as desired.
    '''
    combined_objects = {}
    for o in objects:
        if type(o) is dict:
            for k, v in o.items():
                if combined_objects.get(k) is not None:
                    raise NotUnique(k, combined_objects)
                combined_objects[k] = v
        elif hasattr(o, 'name'):
            if combined_objects.get(o.name) is not None:
                raise NotUnique(o.name, combined_objects)
            combined_objects[o.name] = o
        else:
            if o is not None:
                raise RuntimeError('expected a list of dict or list of list, got a type {}'.format(type(o)))
    return combined_objects


class _Mapped(object):
    '''_Mapped is a helper class that replaces spaces and dashes
    in the name of an object and assigns the object as an attribute

         input: {'my org': Organization}
         output: instance.my_org = Organization
    '''
    def __init__(self, d):
        self.d = d
        for k,v in d.items():
            k = k.replace(' ', '_')
            k = k.replace('-', '_')

            setattr(self, k.replace(' ','_'), v)

    def all(self):
        return self.d.values()

