class Common(Exception):
    def __init__(self, status_string='', message=''):
        if isinstance(status_string, Exception):
            self.status_string = ''
            return super(Common, self).__init__(*status_string)
        self.status_string = status_string
        self.msg = message

    def __getitem__(self, val):
        return (self.status_string, self.msg)[val]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '{} - {}'.format(self.status_string, self.msg)


class BadRequest(Common):

    pass


class Conflict(Common):

    pass


class Duplicate(Common):

    pass


class Forbidden(Common):

    pass


class InternalServerError(Common):

    pass


class BadGateway(Common):

    pass


class LicenseExceeded(Common):

    pass


class LicenseInvalid(Common):

    pass


class MethodNotAllowed(Common):

    pass


class NoContent(Common):

    message = ''


class NotFound(Common):

    pass


class PaymentRequired(Common):

    pass


class Unauthorized(Common):

    pass


class Unknown(Common):

    pass


class WaitUntilTimeout(Common):

    pass


class UnexpectedAWXState(Common):

    pass


class IsMigrating(Common):

    pass


class ImportExportError(Exception):

    pass
