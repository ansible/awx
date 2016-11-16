# Helps with test cases.
# Save all components of a uri (i.e. scheme, username, password, etc.) so that
# when we construct a uri string and decompose it, we can verify the decomposition


class URI(object):
    DEFAULTS = {
        'scheme' : 'http',
        'username' : 'MYUSERNAME',
        'password' : 'MYPASSWORD',
        'host' : 'host.com',
    }

    def __init__(self, description='N/A', scheme=DEFAULTS['scheme'], username=DEFAULTS['username'], password=DEFAULTS['password'], host=DEFAULTS['host']):
        self.description = description
        self.scheme = scheme
        self.username = username
        self.password = password
        self.host = host

    def get_uri(self):
        uri = "%s://" % self.scheme
        if self.username:
            uri += "%s" % self.username
        if self.password:
            uri += ":%s" % self.password
        if (self.username or self.password) and self.host is not None:
            uri += "@%s" % self.host
        elif self.host is not None:
            uri += "%s" % self.host
        return uri

    def get_secret_count(self):
        secret_count = 0
        if self.username:
            secret_count += 1
        if self.password:
            secret_count += 1
        return secret_count

    def __string__(self):
        return self.get_uri()

    def __repr__(self):
        return self.get_uri()
