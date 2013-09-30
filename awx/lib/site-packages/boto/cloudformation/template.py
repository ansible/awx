from boto.resultset import ResultSet

class Template:
    def __init__(self, connection=None):
        self.connection = connection
        self.description = None
        self.template_parameters = None

    def startElement(self, name, attrs, connection):
        if name == "Parameters":
            self.template_parameters = ResultSet([('member', TemplateParameter)])
            return self.template_parameters
        else:
            return None

    def endElement(self, name, value, connection):
        if name == "Description":
            self.description = value
        else:
            setattr(self, name, value)

class TemplateParameter:
    def __init__(self, parent):
        self.parent = parent
        self.default_value = None
        self.description = None
        self.no_echo = None
        self.parameter_key = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == "DefaultValue":
            self.default_value = value
        elif name == "Description":
            self.description = value
        elif name == "NoEcho":
            self.no_echo = bool(value)
        elif name == "ParameterKey":
            self.parameter_key = value
        else:
            setattr(self, name, value)
