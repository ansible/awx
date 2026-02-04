import http.client
import socket
import urllib.error
import urllib.request
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def get_dispatcherd_metrics(request):
    metrics_cfg = settings.METRICS_SUBSYSTEM_CONFIG.get('server', {}).get(settings.METRICS_SERVICE_DISPATCHER, {})
    host = metrics_cfg.get('host', 'localhost')
    port = metrics_cfg.get('port', 8015)
    metrics_filter = []
    if request is not None and hasattr(request, "query_params"):
        try:
            nodes_filter = request.query_params.getlist("node")
        except Exception:
            nodes_filter = []
        if nodes_filter and settings.CLUSTER_HOST_ID not in nodes_filter:
            return ''
        try:
            metrics_filter = request.query_params.getlist("metric")
        except Exception:
            metrics_filter = []
    if metrics_filter:
        # Right now we have no way of filtering the dispatcherd metrics
        # so just avoid getting in the way if another metric is filtered for
        return ''
    url = f"http://{host}:{port}/metrics"
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            payload = response.read()
            if not payload:
                return ''
            return payload.decode('utf-8')
    except (urllib.error.URLError, UnicodeError, socket.timeout, TimeoutError, http.client.HTTPException) as exc:
        logger.debug(f"Failed to collect dispatcherd metrics from {url}: {exc}")
        return ''
