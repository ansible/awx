# Copyright (c) 2017 Red Hat, Inc


def transform_dict(dict_map, d):
    return {to_key: d[from_key] for from_key, to_key in dict_map.iteritems()}

