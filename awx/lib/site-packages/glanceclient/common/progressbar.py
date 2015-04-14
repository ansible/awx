# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys

import six


class _ProgressBarBase(object):
    """
    Base abstract class used by specific class wrapper to show a progress bar
    when the wrapped object are consumed.

    :param wrapped: Object to wrap that hold data to be consumed.
    :param totalsize: The total size of the data in the wrapped object.

    :note: The progress will be displayed only if sys.stdout is a tty.
    """

    def __init__(self, wrapped, totalsize):
        self._wrapped = wrapped
        self._totalsize = float(totalsize)
        self._show_progress = sys.stdout.isatty() and self._totalsize != 0
        self._percent = 0

    def _display_progress_bar(self, size_read):
        if self._show_progress:
            self._percent += size_read / self._totalsize
            # Output something like this: [==========>             ] 49%
            sys.stdout.write('\r[{0:<30}] {1:.0%}'.format(
                '=' * int(round(self._percent * 29)) + '>', self._percent
            ))
            sys.stdout.flush()

    def __getattr__(self, attr):
        # Forward other attribute access to the wrapped object.
        return getattr(self._wrapped, attr)


class VerboseFileWrapper(_ProgressBarBase):
    """
    A file wrapper that show and advance a progress bar whenever file's read
    method is called.
    """

    def read(self, *args, **kwargs):
        data = self._wrapped.read(*args, **kwargs)
        if data:
            self._display_progress_bar(len(data))
        else:
            if self._show_progress:
                # Break to a new line from the progress bar for incoming
                # output.
                sys.stdout.write('\n')
        return data


class VerboseIteratorWrapper(_ProgressBarBase):
    """
    An iterator wrapper that show and advance a progress bar whenever
    data is consumed from the iterator.

    :note: Use only with iterator that yield strings.
    """

    def __iter__(self):
        return self

    def next(self):
        try:
            data = six.next(self._wrapped)
            # NOTE(mouad): Assuming that data is a string b/c otherwise calling
            # len function will not make any sense.
            self._display_progress_bar(len(data))
            return data
        except StopIteration:
            if self._show_progress:
                # Break to a new line from the progress bar for incoming
                # output.
                sys.stdout.write('\n')
            raise

    # In Python 3, __next__() has replaced next().
    __next__ = next
