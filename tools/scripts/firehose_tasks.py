#!/usr/bin/env python

from django import setup

from awx import prepare_env

prepare_env()

setup()

# Keeping this in test folder allows it to be importable
from awx.main.tests.data.sleep_task import sleep_task


for i in range(634):
    sleep_task.delay()
