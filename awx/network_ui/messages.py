

from collections import namedtuple


MultipleMessage = namedtuple('MultipleMessage', ['msg_type',
                                                 'messages'])
InterfaceCreate = namedtuple('InterfaceCreate', ['msg_type',
                                                 'sender',
                                                 'device_id',
                                                 'id',
                                                 'name'])
LinkCreate = namedtuple('LinkCreate', ['msg_type',
                                       'sender',
                                       'id',
                                       'name',
                                       'from_device_id',
                                       'to_device_id',
                                       'from_interface_id',
                                       'to_interface_id'])


def to_dict(message):
    if isinstance(message, MultipleMessage):
        d = dict(message._asdict())
        inner_messages = []
        for m in d['messages']:
            inner_messages.append(to_dict(m))
        d['messages'] = inner_messages
        return d
    else:
        return dict(message._asdict())
