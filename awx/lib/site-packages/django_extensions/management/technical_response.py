import six


def null_technical_500_response(request, exc_type, exc_value, tb):
    six.reraise(exc_type, exc_value, tb)

