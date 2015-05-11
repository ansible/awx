from django.core.exceptions import ImproperlyConfigured
from rest_framework import mixins
from rest_framework.generics import GenericAPIView
from mongoengine.django.shortcuts import get_document_or_404


class MongoAPIView(GenericAPIView):
    """
    Mixin for views manipulating mongo documents

    """
    queryset = None
    serializer_class = None
    lookup_field = 'id'

    def get_queryset(self):
        """
        Get the list of items for this view.
        This must be an iterable, and may be a queryset.
        Defaults to using `self.queryset`.

        You may want to override this if you need to provide different
        querysets depending on the incoming request.

        (Eg. return a list of items that is specific to the user)
        """
        if self.queryset is not None:
            return self.queryset.clone()

        if self.model is not None:
            return self.get_serializer().opts.model.objects.all()

        raise ImproperlyConfigured("'%s' must define 'queryset' or 'model'"
                                    % self.__class__.__name__)

    def get_object(self, queryset=None):
        """
        Get a document instance for read/update/delete requests.
        """
        query_key = self.lookup_url_kwarg or self.lookup_field
        query_kwargs = {query_key: self.kwargs[query_key]}
        queryset = self.get_queryset()

        obj = get_document_or_404(queryset, **query_kwargs)
        self.check_object_permissions(self.request, obj)

        return obj


class CreateAPIView(mixins.CreateModelMixin,
                    MongoAPIView):

    """
    Concrete view for creating a model instance.
    """
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  MongoAPIView):
    """
    Concrete view for listing a queryset.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        MongoAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      MongoAPIView):
    """
    Concrete view for retrieving a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    MongoAPIView):

    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            MongoAPIView):
    """
    Concrete view for retrieving, updating a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             MongoAPIView):
    """
    Concrete view for retrieving or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   MongoAPIView):
    """
    Concrete view for retrieving, updating or deleting a model instance.
    """
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)