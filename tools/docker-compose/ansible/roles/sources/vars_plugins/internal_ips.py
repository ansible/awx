import socket


def internal_ips():
    # Pulled from https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#configure-internal-ips
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    internal_ips = [ip[: ip.rfind(".")] + ".1" for ip in ips] + ["127.0.0.1", "10.0.2.2"]

    return internal_ips


class VarsModule(object):
    def get_vars(self, loader, path, entities):
        return {'internal_ips': internal_ips()}
