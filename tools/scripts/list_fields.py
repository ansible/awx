__all__ = ['pretty_print_model_fields']


def _get_class_full_name(cls_):
    return cls_.__module__ + '.' + cls_.__name__


class _ModelFieldRow(object):

    def __init__(self, field):
        self.field = field
        self.name = field.name
        self.type_ = _get_class_full_name(type(field))
        if self.field.many_to_many\
                or self.field.many_to_one\
                or self.field.one_to_many\
                or self.field.one_to_one:
            self.related_model = _get_class_full_name(self.field.remote_field.model)
        else:
            self.related_model = 'N/A'

    def pretty_print(self, max_name_len, max_type_len, max_rel_model_len):
        row = []
        row.append(self.name)
        row.append(' ' * (max_name_len - len(self.name)))
        row.append('|')
        row.append(self.type_)
        row.append(' ' * (max_type_len - len(self.type_)))
        row.append('|')
        row.append(self.related_model)
        row.append(' ' * (max_rel_model_len - len(self.related_model)))
        print(''.join(row))


def pretty_print_model_fields(model):
    field_info_rows = []
    max_lens = [0, 0, 0]
    for field in model._meta.get_fields():
        field_info_rows.append(_ModelFieldRow(field))
        max_lens[0] = max(max_lens[0], len(field_info_rows[-1].name))
        max_lens[1] = max(max_lens[1], len(field_info_rows[-1].type_))
        max_lens[2] = max(max_lens[2], len(field_info_rows[-1].related_model))
    print('=' * (sum(max_lens) + len(max_lens) - 1))
    for row in field_info_rows:
        row.pretty_print(*max_lens)
        print('=' * (sum(max_lens) + len(max_lens) - 1))
