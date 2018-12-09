# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import shutil

from coverage.misc import CoverageException
from django.http import HttpResponse, Http404
from django.shortcuts import render, render_to_response
from django.template import loader

from .cov import cov

def start_coverage(request):
    cov.erase()
    cov.start()
    return HttpResponse('Started data collection for code coverage')

def stop_coverage(request):
    cov.stop()
    cov.save()
    cov.combine()
    try:
        cov.html_report(directory='awx/maximum_parsimony/htmlcov')
    except CoverageException:
        raise Http404("""
            Insufficient data collected to create report.
            If you have not started data collection, do so at /coverage/start/
            If you have started data collection, you just need to excercise the application more,
            or not rapidly toggle between /coverage/start/ and /coverage/stop/
            """)
    return HttpResponse('Stopped and saved data from code coverage')

def report(request):
    if not os.path.isfile('awx/maximum_parsimony/htmlcov/index.html'):
        raise Http404("""
            No html report exists yet.
            Start coverage with GET to /coverage/start/
            Stop, save, and generate report with GET to /coverage/stop/
            THEN you may view html report here.
            """
            )
    template = loader.get_template('index.html')
    return HttpResponse(template.render())

def clean(request):
    cov.stop()
    cov.erase()
    if os.path.isdir('awx/maximum_parsimony/htmlcov'):
        shutil.rmtree('awx/maximum_parsimony/htmlcov')
        return HttpResponse('Stopped coverage collection and removed all existing coverage files and reports')
    return HttpResponse('Stopped coverage collection and removed all existing coverage files')
