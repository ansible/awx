from django.shortcuts import render
from django import forms
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import yaml


# Create your views here.
from .models import Topology
from .serializers import topology_data


def index(request):
    return render(request, "network_ui/index.html", dict(topologies=Topology.objects.all().order_by('-pk')))


class TopologyForm(forms.Form):
    topology_id = forms.IntegerField()


def json_topology_data(request):
    form = TopologyForm(request.GET)
    if form.is_valid():
        return JsonResponse(topology_data(form.cleaned_data['topology_id']))
    else:
        return HttpResponseBadRequest(form.errors)


def yaml_topology_data(request):
    form = TopologyForm(request.GET)
    if form.is_valid():
        return HttpResponse(yaml.safe_dump(topology_data(form.cleaned_data['topology_id']), default_flow_style=False))
    else:
        return HttpResponseBadRequest(form.errors)

