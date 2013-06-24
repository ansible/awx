def load_ipython_extension(ipython):
    from django.core.management.color import no_style
    from django_extensions.management.shells import import_objects
    imported_objects = import_objects(options={'dont_load': []},
                                      style=no_style())
    ipython.push(imported_objects)
