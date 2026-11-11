# AWX
from awx.api.generics import SubListCreateAttachDetachAPIView, RetrieveUpdateAPIView, ListCreateAPIView
from awx.main.models import Label
from awx.api.serializers import LabelSerializer
from ansible_base.lib.utils.schema import extend_schema_if_available

# Django
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

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
    resource_purpose = 'labels of a resource'

    def unattach(self, request, *args, **kwargs):
        sub_id, res = super().unattach_validate(request)
        if res:
            return res

        res = super().unattach_by_id(request, sub_id)

        obj = self.model.objects.get(id=sub_id)

        if obj.is_detached():
            obj.delete()

        return res

    @extend_schema_if_available(extensions={"x-ai-description": "Create or attach a label to a resource"})
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

        # Give a 400 error if we have attached too many labels to this object.
        # Disassociation is handled by the parent post() and must remain available
        # so an object over the limit can be recovered.
        if 'disassociate' not in request.data:
            label_filter = self.parent_model._meta.get_field(self.relationship).remote_field.name
            label_id = request.data.get('id')
            # Let the generic attach validator return its normal 400 response
            # for malformed IDs before they are used in an ORM filter.
            if label_id is None or isinstance(label_id, int):
                label_counts = Label.objects.filter(**{label_filter: self.kwargs['pk']}).aggregate(
                    total=Count('pk'), requested=Count('pk', filter=Q(pk=label_id))
                )
                if label_counts['total'] >= 100 and not label_counts['requested']:
                    return Response(
                        dict(msg=_(f'Maximum number of labels for {self.parent_model._meta.verbose_name_raw} reached.')), status=HTTP_400_BAD_REQUEST
                    )

        return super().post(request, *args, **kwargs)


class LabelDetail(RetrieveUpdateAPIView):
    model = Label
    serializer_class = LabelSerializer
    resource_purpose = 'label detail'


class LabelList(ListCreateAPIView):
    name = _("Labels")
    model = Label
    serializer_class = LabelSerializer
    resource_purpose = 'labels'
