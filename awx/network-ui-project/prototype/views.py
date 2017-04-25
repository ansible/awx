from django.shortcuts import render

# Create your views here.
from .models import Topology


def index(request):
    return render(request, "prototype/index.html", dict(topologies=Topology.objects.all().order_by('-pk')))
