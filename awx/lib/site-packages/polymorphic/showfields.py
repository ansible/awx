# -*- coding: utf-8 -*-

from django.db import models
from django.utils import six

class ShowFieldBase(object):
    """ base class for the ShowField... model mixins, does the work """

    polymorphic_query_multiline_output = True  # cause nicer multiline PolymorphicQuery output

    polymorphic_showfield_type = False
    polymorphic_showfield_content = False

    # these may be overridden by the user
    polymorphic_showfield_max_line_width = None
    polymorphic_showfield_max_field_width = 20
    polymorphic_showfield_old_format = False

    def __repr__(self):
        return self.__unicode__()

    def _showfields_get_content(self, field_name, field_type=type(None)):
        "helper for __unicode__"
        content = getattr(self, field_name)
        if self.polymorphic_showfield_old_format:
            out = ': '
        else:
            out = ' '
        if issubclass(field_type, models.ForeignKey):
            if content is None:
                out += 'None'
            else:
                out += content.__class__.__name__
        elif issubclass(field_type, models.ManyToManyField):
            out += '%d' % content.count()
        elif isinstance(content, six.integer_types):
            out += str(content)
        elif content is None:
            out += 'None'
        else:
            txt = str(content)
            if len(txt) > self.polymorphic_showfield_max_field_width:
                txt = txt[:self.polymorphic_showfield_max_field_width - 2] + '..'
            out += '"' + txt + '"'
        return out

    def _showfields_add_regular_fields(self, parts):
        "helper for __unicode__"
        done_fields = set()
        for field in self._meta.fields + self._meta.many_to_many:
            if field.name in self.polymorphic_internal_model_fields or '_ptr' in field.name:
                continue
            if field.name in done_fields:
                continue  # work around django diamond inheritance problem
            done_fields.add(field.name)

            out = field.name

            # if this is the standard primary key named "id", print it as we did with older versions of django_polymorphic
            if field.primary_key and field.name == 'id' and type(field) == models.AutoField:
                out += ' ' + str(getattr(self, field.name))

            # otherwise, display it just like all other fields (with correct type, shortened content etc.)
            else:
                if self.polymorphic_showfield_type:
                    out += ' (' + type(field).__name__
                    if field.primary_key:
                        out += '/pk'
                    out += ')'

                if self.polymorphic_showfield_content:
                    out += self._showfields_get_content(field.name, type(field))

            parts.append((False, out, ','))

    def _showfields_add_dynamic_fields(self, field_list, title, parts):
        "helper for __unicode__"
        parts.append((True, '- ' + title, ':'))
        for field_name in field_list:
            out = field_name
            content = getattr(self, field_name)
            if self.polymorphic_showfield_type:
                out += ' (' + type(content).__name__ + ')'
            if self.polymorphic_showfield_content:
                out += self._showfields_get_content(field_name)

            parts.append((False, out, ','))

    def __unicode__(self):
        # create list ("parts") containing one tuple for each title/field:
        # ( bool: new section , item-text , separator to use after item )

        # start with model name
        parts = [(True, self.__class__.__name__, ':')]

        # add all regular fields
        self._showfields_add_regular_fields(parts)

        # add annotate fields
        if hasattr(self, 'polymorphic_annotate_names'):
            self._showfields_add_dynamic_fields(self.polymorphic_annotate_names, 'Ann', parts)

        # add extra() select fields
        if hasattr(self, 'polymorphic_extra_select_names'):
            self._showfields_add_dynamic_fields(self.polymorphic_extra_select_names, 'Extra', parts)

        # format result

        indent = len(self.__class__.__name__) + 5
        indentstr = ''.rjust(indent)
        out = ''
        xpos = 0
        possible_line_break_pos = None

        for i in range(len(parts)):
            new_section, p, separator = parts[i]
            final = (i == len(parts) - 1)
            if not final:
                next_new_section, _, _ = parts[i + 1]

            if (self.polymorphic_showfield_max_line_width
                and xpos + len(p) > self.polymorphic_showfield_max_line_width
                and possible_line_break_pos != None):
                rest = out[possible_line_break_pos:]
                out = out[:possible_line_break_pos]
                out += '\n' + indentstr + rest
                xpos = indent + len(rest)

            out += p
            xpos += len(p)

            if not final:
                if not next_new_section:
                    out += separator
                    xpos += len(separator)
                out += ' '
                xpos += 1

            if not new_section:
                possible_line_break_pos = len(out)

        return '<' + out + '>'


class ShowFieldType(ShowFieldBase):
    """ model mixin that shows the object's class and it's field types """
    polymorphic_showfield_type = True


class ShowFieldContent(ShowFieldBase):
    """ model mixin that shows the object's class, it's fields and field contents """
    polymorphic_showfield_content = True


class ShowFieldTypeAndContent(ShowFieldBase):
    """ model mixin, like ShowFieldContent, but also show field types """
    polymorphic_showfield_type = True
    polymorphic_showfield_content = True


# compatibility with old class names
ShowFieldTypes = ShowFieldType
ShowFields = ShowFieldContent
ShowFieldsAndTypes = ShowFieldTypeAndContent
