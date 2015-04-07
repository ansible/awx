import textwrap

from stevedore.example import base


class FieldList(base.FormatterBase):
    """Format values as a reStructuredText field list.

    For example::

      : name1 : value
      : name2 : value
      : name3 : a long value
          will be wrapped with
          a hanging indent
    """

    def format(self, data):
        """Format the data and return unicode text.

        :param data: A dictionary with string keys and simple types as
                     values.
        :type data: dict(str:?)
        """
        for name, value in sorted(data.items()):
            full_text = ': {name} : {value}'.format(
                name=name,
                value=value,
            )
            wrapped_text = textwrap.fill(
                full_text,
                initial_indent='',
                subsequent_indent='    ',
                width=self.max_width,
            )
            yield wrapped_text + '\n'
