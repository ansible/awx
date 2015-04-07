import abc

import six


@six.add_metaclass(abc.ABCMeta)
class FormatterBase(object):
    """Base class for example plugin used in the tutoral.
    """

    def __init__(self, max_width=60):
        self.max_width = max_width

    @abc.abstractmethod
    def format(self, data):
        """Format the data and return unicode text.

        :param data: A dictionary with string keys and simple types as
                     values.
        :type data: dict(str:?)
        :returns: Iterable producing the formatted text.
        """
