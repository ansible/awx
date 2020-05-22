## CORS Support

AWX supports custom CORS headers via the Django CORS Middleware
(https://github.com/ottoyiu/django-cors-headers)

To define CORS-specific settings, add them to ``/etc/tower/conf.d/cors.py``:

```python
CORS_ORIGIN_WHITELIST = (
    'hostname.example.com',
    '127.0.0.1:9000'
)
```

...and restart all AWX services for changes to take effect.
