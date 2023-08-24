# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

import datetime
import io
import ipaddress
import os
import tarfile
import time
import re

import asn1
from awx.api import serializers
from awx.api.generics import GenericAPIView, Response
from awx.api.permissions import IsSystemAdminOrAuditor
from awx.main import models
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import DNSName, IPAddress, ObjectIdentifier, OtherName
from cryptography.x509.oid import NameOID
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from rest_framework import status

# Red Hat has an OID namespace (RHANANA). Receptor has its own designation under that.
RECEPTOR_OID = "1.3.6.1.4.1.2312.19.1"


# generate install bundle for the instance
# install bundle directory structure
# ├── install_receptor.yml (playbook)
# ├── inventory.yml
# ├── group_vars
# │   └── all.yml
# ├── receptor
# │   ├── tls
# │   │   ├── ca
# │   │   │   └── receptor-ca.crt
# │   │   ├── receptor.crt
# │   │   └── receptor.key
# │   └── work-public-key.pem
# └── requirements.yml


class InstanceInstallBundle(GenericAPIView):
    name = _('Install Bundle')
    model = models.Instance
    serializer_class = serializers.InstanceSerializer
    permission_classes = (IsSystemAdminOrAuditor,)

    def get(self, request, *args, **kwargs):
        instance_obj = self.get_object()

        if instance_obj.node_type not in ('execution', 'hop'):
            return Response(
                data=dict(msg=_('Install bundle can only be generated for execution or hop nodes.')),
                status=status.HTTP_400_BAD_REQUEST,
            )

        with io.BytesIO() as f:
            with tarfile.open(fileobj=f, mode='w:gz') as tar:
                # copy /etc/receptor/tls/ca/mesh-CA.crt to receptor/tls/ca in the tar file
                tar.add(os.path.realpath('/etc/receptor/tls/ca/mesh-CA.crt'), arcname=f"{instance_obj.hostname}_install_bundle/receptor/tls/ca/mesh-CA.crt")

                # copy /etc/receptor/work_public_key.pem to receptor/work_public_key.pem
                tar.add('/etc/receptor/work_public_key.pem', arcname=f"{instance_obj.hostname}_install_bundle/receptor/work_public_key.pem")

                # generate and write the receptor key to receptor/tls/receptor.key in the tar file
                key, cert = generate_receptor_tls(instance_obj)

                def tar_addfile(tarinfo, filecontent):
                    tarinfo.mtime = time.time()
                    tarinfo.size = len(filecontent)
                    tar.addfile(tarinfo, io.BytesIO(filecontent))

                key_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/receptor/tls/receptor.key")
                tar_addfile(key_tarinfo, key)

                cert_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/receptor/tls/receptor.crt")
                cert_tarinfo.size = len(cert)
                tar_addfile(cert_tarinfo, cert)

                # generate and write install_receptor.yml to the tar file
                playbook = generate_playbook(instance_obj).encode('utf-8')
                playbook_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/install_receptor.yml")
                tar_addfile(playbook_tarinfo, playbook)

                # generate and write inventory.yml to the tar file
                inventory_yml = generate_inventory_yml(instance_obj).encode('utf-8')
                inventory_yml_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/inventory.yml")
                tar_addfile(inventory_yml_tarinfo, inventory_yml)

                # generate and write group_vars/all.yml to the tar file
                group_vars = generate_group_vars_all_yml(instance_obj).encode('utf-8')
                group_vars_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/group_vars/all.yml")
                tar_addfile(group_vars_tarinfo, group_vars)

                # generate and write requirements.yml to the tar file
                requirements_yml = generate_requirements_yml().encode('utf-8')
                requirements_yml_tarinfo = tarfile.TarInfo(f"{instance_obj.hostname}_install_bundle/requirements.yml")
                tar_addfile(requirements_yml_tarinfo, requirements_yml)

            # respond with the tarfile
            f.seek(0)
            response = HttpResponse(f.read(), status=status.HTTP_200_OK)
            response['Content-Disposition'] = f"attachment; filename={instance_obj.hostname}_install_bundle.tar.gz"
            return response


def generate_playbook(instance_obj):
    playbook_yaml = render_to_string("instance_install_bundle/install_receptor.yml", context=dict(instance=instance_obj))
    # convert consecutive newlines with a single newline
    return re.sub(r'\n+', '\n', playbook_yaml)


def generate_requirements_yml():
    return render_to_string("instance_install_bundle/requirements.yml")


def generate_inventory_yml(instance_obj):
    return render_to_string("instance_install_bundle/inventory.yml", context=dict(instance=instance_obj))


def generate_group_vars_all_yml(instance_obj):
    peers = []
    for instance in instance_obj.peers.all():
        peers.append(dict(host=instance.hostname, port=instance.listener_port))
    all_yaml = render_to_string("instance_install_bundle/group_vars/all.yml", context=dict(instance=instance_obj, peers=peers))
    # convert consecutive newlines with a single newline
    return re.sub(r'\n+', '\n', all_yaml)


def generate_receptor_tls(instance_obj):
    # generate private key for the receptor
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # encode receptor hostname to asn1
    hostname = instance_obj.hostname
    encoder = asn1.Encoder()
    encoder.start()
    encoder.write(hostname.encode(), nr=asn1.Numbers.UTF8String)
    hostname_asn1 = encoder.output()

    san_params = [
        DNSName(hostname),
        OtherName(ObjectIdentifier(RECEPTOR_OID), hostname_asn1),
    ]

    try:
        san_params.append(IPAddress(ipaddress.IPv4Address(hostname)))
    except ipaddress.AddressValueError:
        pass

    # generate certificate for the receptor
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, hostname),
                ]
            )
        )
        .add_extension(
            x509.SubjectAlternativeName(san_params),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    # sign csr with the receptor ca key from /etc/receptor/ca/mesh-CA.key
    with open('/etc/receptor/tls/ca/mesh-CA.key', 'rb') as f:
        ca_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
        )

    with open('/etc/receptor/tls/ca/mesh-CA.crt', 'rb') as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())

    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.issuer)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
        .add_extension(
            csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value,
            critical=csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).critical,
        )
        .sign(ca_key, hashes.SHA256())
    )

    key = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    cert = cert.public_bytes(
        encoding=serialization.Encoding.PEM,
    )

    return key, cert
