from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from awx.api.versioning import reverse


class ReceptorAddress(models.Model):
    class Meta:
        app_label = 'main'
        constraints = [
            models.UniqueConstraint(
                fields=["address", "protocol"],
                name="unique_receptor_address",
                violation_error_message=_("Receptor address + protocol must be unique."),
            )
        ]

    class Protocols(models.TextChoices):
        TCP = 'tcp', 'TCP'
        WS = 'ws', 'WS'
        WSS = 'wss', 'WSS'

    address = models.CharField(help_text=_("Routable address for this instance."), max_length=255)
    port = models.IntegerField(help_text=_("Port for the address."), default=27199, validators=[MinValueValidator(0), MaxValueValidator(65535)])
    protocol = models.CharField(
        help_text=_("Protocol to use when connecting, 'tcp', 'wss', or 'ws'."), max_length=10, default=Protocols.TCP, choices=Protocols.choices
    )
    websocket_path = models.CharField(help_text=_("Websocket path."), max_length=255, default="", blank=True)
    is_internal = models.BooleanField(help_text=_("If True, only routable inside of the Kubernetes cluster."), default=False)
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
        if self.protocol == "ws":
            scheme = "wss://"

        if self.protocol == "ws" and self.websocket_path:
            path = f"/{self.websocket_path}"

        if self.port:
            port = f":{self.port}"

        return f"{scheme}{self.address}{port}{path}"

    def get_peer_type(self):
        if self.protocol == 'tcp':
            return 'tcp-peer'
        elif self.protocol in ['ws', 'wss']:
            return 'ws-peer'
        else:
            return None

    def get_absolute_url(self, request=None):
        return reverse('api:receptor_address_detail', kwargs={'pk': self.pk}, request=request)
