from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from awx.api.versioning import reverse


class ReceptorAddress(models.Model):
    class Meta:
        app_label = 'main'
        constraints = [
            models.UniqueConstraint(
                fields=["address"],
                name="unique_receptor_address",
                violation_error_message=_("Receptor address must be unique."),
            )
        ]

    address = models.CharField(help_text=_("Routable address for this instance."), max_length=255)
    port = models.IntegerField(help_text=_("Port for the address."), default=27199, validators=[MinValueValidator(0), MaxValueValidator(65535)])
    websocket_path = models.CharField(help_text=_("Websocket path."), max_length=255, default="", blank=True)
    k8s_routable = models.BooleanField(help_text=_("If True, only routable inside of the Kubernetes cluster."), default=False)
    canonical = models.BooleanField(help_text=_("If True, this address is the canonical address for the instance."), default=False)
    managed = models.BooleanField(help_text=_("If True, this address is managed by the control plane."), default=False, editable=False)
    peers_from_control_nodes = models.BooleanField(help_text=_("If True, control plane cluster nodes should automatically peer to it."), default=False)
    instance = models.ForeignKey(
        'Instance',
        related_name='receptor_addresses',
        on_delete=models.CASCADE,
        null=False,
    )

    def __str__(self):
        return self.get_full_address()

    def get_full_address(self):
        scheme = ""
        path = ""
        port = ""
        if self.instance.protocol == "ws":
            scheme = "wss://"

        if self.instance.protocol == "ws" and self.websocket_path:
            path = f"/{self.websocket_path}"

        if self.port:
            port = f":{self.port}"

        return f"{scheme}{self.address}{port}{path}"

    def get_peer_type(self):
        if self.instance.protocol == 'tcp':
            return 'tcp-peer'
        elif self.instance.protocol in ['ws', 'wss']:
            return 'ws-peer'
        else:
            return None

    def get_absolute_url(self, request=None):
        return reverse('api:receptor_address_detail', kwargs={'pk': self.pk}, request=request)
