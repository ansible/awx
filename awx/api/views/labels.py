# AWX
from awx.api.generics import SubListCreateAttachDetachAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from awx.main.models import Label
from awx.api.serializers import LabelSerializer

# Django
from django.utils.translation import gettext_lazy as _

# Django REST Framework
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class LabelSubListCreateAttachDetachView(SubListCreateAttachDetachAPIView):
    """
    For related labels lists like /api/v2/inventories/N/labels/

    We want want the last instance to be deleted from the database
    when the last disassociate happens.

    Subclasses need to define parent_model
    """

    model = Label
    serializer_class = LabelSerializer
    relationship = 'labels'

    def unattach(self, request, *args, **kwargs):
        (sub_id, res) = super().unattach_validate(request)
        if res:
            return res

        res = super().unattach_by_id(request, sub_id)

        obj = self.model.objects.get(id=sub_id)

        if obj.is_detached():
            obj.delete()

        return res

    def post(self, request, *args, **kwargs):
        # If a label already exists in the database, attach it instead of erroring out
        # that it already exists
        if 'id' not in request.data and 'name' in request.data and 'organization' in request.data:
            existing = Label.objects.filter(name=request.data['name'], organization_id=request.data['organization'])
            if existing.exists():
                existing = existing[0]
                request.data['id'] = existing.id
                del request.data['name']
                del request.data['organization']

        # Give a 400 error if we have attached too many labels to this object
        label_filter = self.parent_model._meta.get_field(self.relationship).remote_field.name
        if Label.objects.filter(**{label_filter: self.kwargs['pk']}).count() > 100:
            return Response(dict(msg=_(f'Maximum number of labels for {self.parent_model._meta.verbose_name_raw} reached.')), status=HTTP_400_BAD_REQUEST)

        return super().post(request, *args, **kwargs)


class LabelDetail(RetrieveUpdateAPIView):
    model = Label
    serializer_class = LabelSerializer


class LabelList(ListCreateAPIView):
    name = _("Labels")
    model = Label
    serializer_class = LabelSerializer
