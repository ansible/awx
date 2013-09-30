try:
    __version__ = __import__('pkg_resources').get_distribution('d2to1').version
except:
    __version__ = ''
