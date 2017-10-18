#!/usr/bin/env python
import argparse
from django.apps import apps


def get_class_full_name(cls_):
    return cls_.__module__ + '.' + cls_.__name__


def main(model_name=None):
    for m in apps.get_models():
        print(get_class_full_name(m))
        for field in m._meta.get_fields():
            if field.one_to_many or field.many_to_many or field.many_to_one:
                print("%s, %s" % (field.name, get_class_full_name(type(field))))
        print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-name', type=str,
                        help='Name of the model to check related fields against.',
                        dest='model_name', metavar='STR')
    main(**vars(parser.parse_args()))
