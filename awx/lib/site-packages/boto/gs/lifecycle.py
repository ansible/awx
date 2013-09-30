# Copyright 2013 Google Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

from boto.exception import InvalidLifecycleConfigError

# Relevant tags for the lifecycle configuration XML document.
LIFECYCLE_CONFIG   = 'LifecycleConfiguration'
RULE               = 'Rule'
ACTION             = 'Action'
DELETE             = 'Delete'
CONDITION          = 'Condition'
AGE                = 'Age'
CREATED_BEFORE     = 'CreatedBefore'
NUM_NEWER_VERSIONS = 'NumberOfNewerVersions'
IS_LIVE            = 'IsLive'

# List of all action elements.
LEGAL_ACTIONS = [DELETE]
# List of all action parameter elements.
LEGAL_ACTION_PARAMS = []
# List of all condition elements.
LEGAL_CONDITIONS = [AGE, CREATED_BEFORE, NUM_NEWER_VERSIONS, IS_LIVE]
# Dictionary mapping actions to supported action parameters for each action.
LEGAL_ACTION_ACTION_PARAMS = {
    DELETE: [],
}

class Rule(object):
    """
    A lifecycle rule for a bucket.

    :ivar action: Action to be taken.

    :ivar action_params: A dictionary of action specific parameters. Each item
    in the dictionary represents the name and value of an action parameter.

    :ivar conditions: A dictionary of conditions that specify when the action
    should be taken. Each item in the dictionary represents the name and value
    of a condition.
    """

    def __init__(self, action=None, action_params=None, conditions=None):
        self.action = action
        self.action_params = action_params or {}
        self.conditions = conditions or {}

        # Name of the current enclosing tag (used to validate the schema).
        self.current_tag = RULE

    def validateStartTag(self, tag, parent):
        """Verify parent of the start tag."""
        if self.current_tag != parent:
            raise InvalidLifecycleConfigError(
                'Invalid tag %s found inside %s tag' % (tag, self.current_tag))

    def validateEndTag(self, tag):
        """Verify end tag against the start tag."""
        if tag != self.current_tag:
            raise InvalidLifecycleConfigError(
                'Mismatched start and end tags (%s/%s)' %
                (self.current_tag, tag))

    def startElement(self, name, attrs, connection):
        if name == ACTION:
            self.validateStartTag(name, RULE)
        elif name in LEGAL_ACTIONS:
            self.validateStartTag(name, ACTION)
            # Verify there is only one action tag in the rule.
            if self.action is not None:
                raise InvalidLifecycleConfigError(
                    'Only one action tag is allowed in each rule')
            self.action = name
        elif name in LEGAL_ACTION_PARAMS:
            # Make sure this tag is found in an action tag.
            if self.current_tag not in LEGAL_ACTIONS:
                raise InvalidLifecycleConfigError(
                    'Tag %s found outside of action' % name)
            # Make sure this tag is allowed for the current action tag.
            if name not in LEGAL_ACTION_ACTION_PARAMS[self.action]:
                raise InvalidLifecycleConfigError(
                    'Tag %s not allowed in action %s' % (name, self.action))
        elif name == CONDITION:
            self.validateStartTag(name, RULE)
        elif name in LEGAL_CONDITIONS:
            self.validateStartTag(name, CONDITION)
            # Verify there is no duplicate conditions.
            if name in self.conditions:
                raise InvalidLifecycleConfigError(
                    'Found duplicate conditions %s' % name)
        else:
            raise InvalidLifecycleConfigError('Unsupported tag ' + name)
        self.current_tag = name

    def endElement(self, name, value, connection):
        self.validateEndTag(name)
        if name == RULE:
            # We have to validate the rule after it is fully populated because
            # the action and condition elements could be in any order.
            self.validate()
        elif name == ACTION:
            self.current_tag = RULE
        elif name in LEGAL_ACTIONS:
            self.current_tag = ACTION
        elif name in LEGAL_ACTION_PARAMS:
            self.current_tag = self.action
            # Add the action parameter name and value to the dictionary.
            self.action_params[name] = value.strip()
        elif name == CONDITION:
            self.current_tag = RULE
        elif name in LEGAL_CONDITIONS:
            self.current_tag = CONDITION
            # Add the condition name and value to the dictionary.
            self.conditions[name] = value.strip()
        else:
            raise InvalidLifecycleConfigError('Unsupported end tag ' + name)

    def validate(self):
        """Validate the rule."""
        if not self.action:
            raise InvalidLifecycleConfigError(
                'No action was specified in the rule')
        if not self.conditions:
            raise InvalidLifecycleConfigError(
                'No condition was specified for action %s' % self.action)

    def to_xml(self):
        """Convert the rule into XML string representation."""
        s = '<' + RULE + '>'
        s += '<' + ACTION + '>'
        if self.action_params:
            s += '<' + self.action + '>'
            for param in LEGAL_ACTION_PARAMS:
                if param in self.action_params:
                    s += ('<' + param + '>' + self.action_params[param] + '</'
                          + param + '>')
            s += '</' + self.action + '>'
        else:
            s += '<' + self.action + '/>'
        s += '</' + ACTION + '>'
        s += '<' + CONDITION + '>'
        for condition in LEGAL_CONDITIONS:
            if condition in self.conditions:
                s += ('<' + condition + '>' + self.conditions[condition] + '</'
                      + condition + '>')
        s += '</' + CONDITION + '>'
        s += '</' + RULE + '>'
        return s

class LifecycleConfig(list):
    """
    A container of rules associated with a lifecycle configuration.
    """

    def __init__(self):
        # Track if root tag has been seen.
        self.has_root_tag = False

    def startElement(self, name, attrs, connection):
        if name == LIFECYCLE_CONFIG:
            if self.has_root_tag:
                raise InvalidLifecycleConfigError(
                    'Only one root tag is allowed in the XML')
            self.has_root_tag = True
        elif name == RULE:
            if not self.has_root_tag:
                raise InvalidLifecycleConfigError('Invalid root tag ' + name)
            rule = Rule()
            self.append(rule)
            return rule
        else:
            raise InvalidLifecycleConfigError('Unsupported tag ' + name)

    def endElement(self, name, value, connection):
        if name == LIFECYCLE_CONFIG:
            pass
        else:
            raise InvalidLifecycleConfigError('Unsupported end tag ' + name)

    def to_xml(self):
        """Convert LifecycleConfig object into XML string representation."""
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<' + LIFECYCLE_CONFIG + '>'
        for rule in self:
            s += rule.to_xml()
        s += '</' + LIFECYCLE_CONFIG + '>'
        return s

    def add_rule(self, action, action_params, conditions):
        """
        Add a rule to this Lifecycle configuration.  This only adds the rule to
        the local copy.  To install the new rule(s) on the bucket, you need to
        pass this Lifecycle config object to the configure_lifecycle method of
        the Bucket object.

        :type action: str
        :param action: Action to be taken.

        :type action_params: dict
        :param action_params: A dictionary of action specific parameters. Each
        item in the dictionary represents the name and value of an action
        parameter.

        :type conditions: dict
        :param conditions: A dictionary of conditions that specify when the
        action should be taken. Each item in the dictionary represents the name
        and value of a condition.
        """
        rule = Rule(action, action_params, conditions)
        self.append(rule)
