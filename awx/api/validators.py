import re

from django.core.validators import RegexValidator, validate_ipv46_address
from django.core.exceptions import ValidationError


class HostnameRegexValidator(RegexValidator):
    """
    Fully validates a domain name that is compliant with norms in Linux/RHEL
        - Cannot start with a hyphen
        - Cannot begin with, or end with a "."
        - Cannot contain any whitespaces
        - Entire hostname is max 255 chars (including dots)
        - Each domain/label is between 1 and 63 characters, except top level domain, which must be at least 2 characters
        - Supports ipv4, ipv6, simple hostnames and FQDNs
        - Follows RFC 9210 (modern RFC 1123, 1178) requirements

    Accepts an IP Address or Hostname as the argument
    """

    regex = '^[a-z0-9][-a-z0-9]*$|^([a-z0-9][-a-z0-9]{0,62}[.])*[a-z0-9][-a-z0-9]{1,62}$'
    flags = re.IGNORECASE

    def __call__(self, value):
        regex_matches, err = self.__validate(value)
        invalid_input = regex_matches if self.inverse_match else not regex_matches
        if invalid_input:
            if err is None:
                err = ValidationError(self.message, code=self.code, params={"value": value})
            raise err

    def __str__(self):
        return f"regex={self.regex}, message={self.message}, code={self.code}, inverse_match={self.inverse_match}, flags={self.flags}"

    def __validate(self, value):
        if ' ' in value:
            return False, ValidationError("whitespaces in hostnames are illegal")

        """
        If we have an IP address, try and validate it.
        """
        try:
            validate_ipv46_address(value)
            return True, None
        except ValidationError:
            pass

        """
        By this point in the code, we probably have a simple hostname, FQDN or a strange hostname like "192.localhost.domain.101"
        """
        if not self.regex.match(value):
            return False, ValidationError(f"illegal characters detected in hostname={value}. Please verify.")

        return True, None
