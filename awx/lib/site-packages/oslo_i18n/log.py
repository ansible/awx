# Copyright 2012 Red Hat, Inc.
# Copyright 2013 IBM Corp.
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

"""logging utilities for translation
"""

from logging import handlers

from oslo_i18n import _translate


class TranslationHandler(handlers.MemoryHandler):
    """Handler that translates records before logging them.

    When lazy translation is enabled in the application (see
    :func:`~oslo_i18n.enable_lazy`), the :class:`TranslationHandler`
    uses its locale configuration setting to determine how to
    translate LogRecord objects before forwarding them to the
    logging.Handler.

    When lazy translation is disabled, the message in the LogRecord is
    converted to unicode without any changes and then forwarded to the
    logging.Handler.

    The handler can be configured declaratively in the
    ``logging.conf`` as follows::

        [handlers]
        keys = translatedlog, translator

        [handler_translatedlog]
        class = handlers.WatchedFileHandler
        args = ('/var/log/api-localized.log',)
        formatter = context

        [handler_translator]
        class = oslo_i18n.log.TranslationHandler
        target = translatedlog
        args = ('zh_CN',)

    If the specified locale is not available in the system, the handler will
    log in the default locale.

    """

    def __init__(self, locale=None, target=None):
        """Initialize a TranslationHandler

        :param locale: locale to use for translating messages
        :param target: logging.Handler object to forward
                       LogRecord objects to after translation
        """
        # NOTE(luisg): In order to allow this handler to be a wrapper for
        # other handlers, such as a FileHandler, and still be able to
        # configure it using logging.conf, this handler has to extend
        # MemoryHandler because only the MemoryHandlers' logging.conf
        # parsing is implemented such that it accepts a target handler.
        handlers.MemoryHandler.__init__(self, capacity=0, target=target)
        self.locale = locale

    def setFormatter(self, fmt):
        self.target.setFormatter(fmt)

    def emit(self, record):
        # We save the message from the original record to restore it
        # after translation, so other handlers are not affected by this
        original_msg = record.msg
        original_args = record.args

        try:
            self._translate_and_log_record(record)
        finally:
            record.msg = original_msg
            record.args = original_args

    def _translate_and_log_record(self, record):
        record.msg = _translate.translate(record.msg, self.locale)

        # In addition to translating the message, we also need to translate
        # arguments that were passed to the log method that were not part
        # of the main message e.g., log.info(_('Some message %s'), this_one))
        record.args = _translate.translate_args(record.args, self.locale)

        self.target.emit(record)
