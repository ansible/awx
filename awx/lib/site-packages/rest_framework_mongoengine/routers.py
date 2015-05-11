from rest_framework.routers import SimpleRouter, DefaultRouter


class MongoRouterMixin(object):
    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        model_cls = getattr(viewset, 'model', None)
        assert model_cls, '`base_name` argument not specified, and could ' \
            'not automatically determine the name from the viewset, as ' \
            'it does not have a `.model` attribute.'
        return model_cls.__name__.lower()


class MongoSimpleRouter(MongoRouterMixin, SimpleRouter):
    pass


class MongoDefaultRouter(MongoSimpleRouter, DefaultRouter):
    pass