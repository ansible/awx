from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
#from rest_framework.renderers import JSONRenderer
#from rest_framework.parsers import JSONParser

from lib.main.models import *
from lib.main.serializers import *
from django.contrib.auth.models import AnonymousUser

from rest_framework import mixins
from rest_framework import generics
from rest_framework import permissions
#from rest_framework.authentication import authentication

# TODO: verify pagination
# TODO: how to add relative resources
# TODO: 

class CustomRbac(permissions.BasePermission):

    def _common_user_check(self, request):
        # no anonymous users
        if type(request.user) == AnonymousUser:
            return False
        # superusers are always good
        if request.user.is_superuser:
            return True
        # other users must have associated acom user records & be active
        acom_user = User.objects.filter(auth_user = request.user)
        if len(acom_user) != 1:
            return False
        if not acom_user[0].active:
            return False
        return True

    def has_permission(self, request, view, obj=None):
        if not self._common_user_check(request):
            return False
        if obj is None:
            return True
        else:
            # haven't tested around these confines yet
            raise Exception("FIXME")

    def has_object_permission(self, request, view, obj):
        if not self._common_user_check(request):
            return False
        # FIXME: TODO: verify the user is actually allowed to see this resource
        return True 

class OrganizationsList(generics.ListCreateAPIView):


    model = Organization
    serializer_class = OrganizationSerializer
    permission_classes = (CustomRbac,)

    #def pre_save(self, obj):
    #   obj.owner = self.request.user
   
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.filter(active=True)
        return Organization.objects.filter(active = True, admins__in = [ self.request.user.application_user ]).distinct() | \
               Organization.objects.filter(active = True, users__in = [ self.request.user.application_user ]).distinct()

 
class OrganizationsDetail(generics.RetrieveUpdateDestroyAPIView):
    model = Organization
    serializer_class = OrganizationSerializer

    permission_classes = (CustomRbac,)

    #def pre_save(self, obj):
    #   obj.owner = self.request.user

#class OrganizationsList(mixins.ListModelMixin, mixins.CreateModelMixin, generics.MultipleObjectAPIView):
#
#    model = Organization
#    serializer_class = OrganizationSerializer
#
#    def get(self, request, *args, **kwargs):
#        return self.list(request, *args, **kwargs)
#
#    def post(self, request, *args, **kwargs):
#        return self.create(request, *args, **kwargs)

#class JSONResponse(HttpResponse):
#    """
#    An HttpResponse that renders it's content into JSON.
#    """
#    def __init__(self, data, **kwargs):
#        content = JSONRenderer().render(data)
#        kwargs['content_type'] = 'application/json'
#        super(JSONResponse, self).__init__(content, **kwargs)

#@csrf_exempt
#def organizations_list(request):
#    """
#    List all code snippets, or create a new snippet.
#    """
#    if request.method == 'GET':
#        # TODO: FILTER
#        organizations = Organization.objects.all()
#        serializer = OrganizationSerializer(organizations, many=True)
#        return JSONResponse(serializer.data)
#
#    elif request.method == 'POST':
#        data = JSONParser().parse(request)
#        # TODO: DATA AUDIT
#        serializer = OrganizationSerializer(data=data)
#        if serializer.is_valid():
#            serializer.save()
#            return JSONResponse(serializer.data, status=201)
#        else:
#            return JSONResponse(serializer.errors, status=400)

#@csrf_exempt
#def snippet_detail(request, pk):
#    """
#    Retrieve, update or delete a code snippet.
#    """
#    try:
#        snippet = Snippet.objects.get(pk=pk)
#    except Snippet.DoesNotExist:
#        return HttpResponse(status=404)
#
#    if request.method == 'GET':
#        serializer = SnippetSerializer(snippet)
#        return JSONResponse(serializer.data)
#
#    elif request.method == 'PUT':
#        data = JSONParser().parse(request)
#        serializer = SnippetSerializer(snippet, data=data)
#        if serializer.is_valid():
#            serializer.save()
#            return JSONResponse(serializer.data)
#        else:
#            return JSONResponse(serializer.errors, status=400)
#
#    elif request.method == 'DELETE':
#        snippet.delete()
#        return HttpResponse(status=204)


