# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

import os
import tarfile
import tempfile

from awx.api import serializers
from awx.api.generics import GenericAPIView, Response
from awx.api.permissions import IsSystemAdminOrAuditor
from awx.main import models
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from django.http import HttpResponse

# generate install bundle for the instance
class InstanceInstallBundle(GenericAPIView):

    name = _('Install Bundle')
    model = models.Instance
    serializer_class = serializers.InstanceSerializer
    permission_classes = (IsSystemAdminOrAuditor,)

    def get(self, request, *args, **kwargs):
        instance_obj = self.get_object()

        # if the instance is not a hop or execution node than return 400
        if instance_obj.node_type not in ('execution', 'hop'):
            return Response(
                data=dict(msg=_('Install bundle can only be generated for execution or hop nodes.')),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # TODO: add actual data into the bundle
        # create a named temporary file directory to store the content of the install bundle
        with tempfile.TemporaryDirectory() as tmpdirname:
            # create a empty file named "moc_content.txt" in the temporary directory
            with open(os.path.join(tmpdirname, 'mock_content.txt'), 'w') as f:
                f.write('mock content')

            # create empty directory in temporary directory
            os.mkdir(os.path.join(tmpdirname, 'mock_dir'))

            # tar.gz and create a temporary file from the temporary directory
            # the directory will be renamed and prefixed with the hostname of the instance
            with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmpfile:
                with tarfile.open(tmpfile.name, 'w:gz') as tar:
                    tar.add(tmpdirname, arcname=f"{instance_obj.hostname}_install_bundle")

                # read the temporary file and send it to the client
                with open(tmpfile.name, 'rb') as f:
                    response = HttpResponse(f.read(), status=status.HTTP_200_OK)
                    response['Content-Disposition'] = f"attachment; filename={instance_obj.hostname}_install_bundle.tar.gz"
                    return response
