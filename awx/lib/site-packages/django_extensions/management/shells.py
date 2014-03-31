import six
import traceback


class ObjectImportError(Exception):
    pass


def import_items(import_directives):
    """
    Import the items in import_directives and return a list of the imported items

    Each item in import_directives should be one of the following forms
        * a tuple like ('module.submodule', ('classname1', 'classname2')), which indicates a 'from module.submodule import classname1, classname2'
        * a tuple like ('module.submodule', 'classname1'), which indicates a 'from module.submodule import classname1'
        * a tuple like ('module.submodule', '*'), which indicates a 'from module.submodule import *'
        * a simple 'module.submodule' which indicates 'import module.submodule'.

    Returns a dict mapping the names to the imported items
    """
    imported_objects = {}
    for directive in import_directives:
        try:
            # First try a straight import
            if type(directive) is str:
                imported_object = __import__(directive)
                imported_objects[directive.split('.')[0]] = imported_object
                print("import %s" % directive)
                continue
            try:
                # Try the ('module.submodule', ('classname1', 'classname2')) form
                for name in directive[1]:
                    imported_object = getattr(__import__(directive[0], {}, {}, name), name)
                    imported_objects[name] = imported_object
                print("from %s import %s" % (directive[0], ', '.join(directive[1])))
                # If it is a tuple, but the second item isn't a list, so we have something like ('module.submodule', 'classname1')
            except AttributeError:
                # Check for the special '*' to import all
                if directive[1] == '*':
                    imported_object = __import__(directive[0], {}, {}, directive[1])
                    for k in dir(imported_object):
                        imported_objects[k] = getattr(imported_object, k)
                    print("from %s import *" % directive[0])
                else:
                    imported_object = getattr(__import__(directive[0], {}, {}, directive[1]), directive[1])
                    imported_objects[directive[1]] = imported_object
                    print("from %s import %s" % (directive[0], directive[1]))
        except ImportError:
            try:
                print("Unable to import %s" % directive)
            except TypeError:
                print("Unable to import %s from %s" % directive)

    return imported_objects


def import_objects(options, style):
    # XXX: (Temporary) workaround for ticket #1796: force early loading of all
    # models from installed apps. (this is fixed by now, but leaving it here
    # for people using 0.96 or older trunk (pre [5919]) versions.
    from django.db.models.loading import get_models, get_apps
    mongoengine = False
    try:
        from mongoengine.base import _document_registry
        mongoengine = True
    except:
        pass

    loaded_models = get_models()  # NOQA

    from django.conf import settings
    imported_objects = {}

    dont_load_cli = options.get('dont_load')  # optparse will set this to [] if it doensnt exists
    dont_load_conf = getattr(settings, 'SHELL_PLUS_DONT_LOAD', [])
    dont_load = dont_load_cli + dont_load_conf
    quiet_load = options.get('quiet_load')

    model_aliases = getattr(settings, 'SHELL_PLUS_MODEL_ALIASES', {})

    # Perform pre-imports before any other imports
    imports = import_items(getattr(settings, 'SHELL_PLUS_PRE_IMPORTS', {}))
    for k, v in six.iteritems(imports):
        imported_objects[k] = v

    load_models = {}

    if getattr(settings, 'SHELL_PLUS_DJANGO_IMPORTS', True):
        load_models.update({
            'django.core.cache': ['cache'],
            'django.core.urlresolvers': ['reverse'],
            'django.conf': ['settings'],
            'django.db': ['transaction'],
            'django.db.models': ['Avg', 'Count', 'F', 'Max', 'Min', 'Sum', 'Q'],
            'django.utils': ['timezone'],
        })

    if mongoengine:
        for name, mod in six.iteritems(_document_registry):
            name = name.split('.')[-1]
            app_name = mod.__module__.split('.')[-2]
            if app_name in dont_load or ("%s.%s" % (app_name, name)) in dont_load:
                continue

            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(name)

    for app_mod in get_apps():
        app_models = get_models(app_mod)
        if not app_models:
            continue

        app_name = app_mod.__name__.split('.')[-2]
        if app_name in dont_load:
            continue

        app_aliases = model_aliases.get(app_name, {})
        for mod in app_models:
            if "%s.%s" % (app_name, mod.__name__) in dont_load:
                continue

            load_models.setdefault(mod.__module__, [])
            load_models[mod.__module__].append(mod.__name__)

    for app_mod, models in sorted(six.iteritems(load_models)):
        app_name = app_mod.split('.')[-2]
        app_aliases = model_aliases.get(app_name, {})
        model_labels = []

        for model_name in sorted(models):
            try:
                imported_object = getattr(__import__(app_mod, {}, {}, model_name), model_name)

                if "%s.%s" % (app_name, model_name) in dont_load:
                    continue

                alias = app_aliases.get(model_name, model_name)
                imported_objects[alias] = imported_object
                if model_name == alias:
                    model_labels.append(model_name)
                else:
                    model_labels.append("%s (as %s)" % (model_name, alias))

            except AttributeError as e:
                if options.get("traceback"):
                    traceback.print_exc()
                if not quiet_load:
                    print(style.ERROR("Failed to import '%s' from '%s' reason: %s" % (model_name, app_mod, str(e))))
                continue

        if not quiet_load:
            print(style.SQL_COLTYPE("from %s import %s" % (app_mod, ", ".join(model_labels))))

    # Perform post-imports after any other imports
    imports = import_items(getattr(settings, 'SHELL_PLUS_POST_IMPORTS', {}))
    for k, v in six.iteritems(imports):
        imported_objects[k] = v

    return imported_objects
