
class _Settings(object):

    def __init__(self):
        self.SERVER = 'https://meganuke:3000/'
        self.NETWORKING_API = 'network_ui/api/'
        self.API_VERSION = 'v1'
        self.SSL_VERIFY = False
        self.user = None
        self.password = None

settings = _Settings()
