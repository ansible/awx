### default json loaders
try:
    import simplejson as json
    json_decimal_args = {"use_decimal": True}  # pragma: no cover
except ImportError:
    import json
    import decimal

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return super(DecimalEncoder, self).default(o)
    json_decimal_args = {"cls": DecimalEncoder}

def default_json_dumps(data):
    return json.dumps(data, separators=(',', ':'),
                      **json_decimal_args)

def default_json_loads(data):
    return json.loads(data)
