#!/usr/bin/env python
import cProfile
import os
import sys
import time

import django

base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

if base_dir not in sys.path:
    sys.path.insert(1, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awx.settings.development")
django.setup()

# Monkey-patch out websocket notifications since we don't have redis running
import awx.main.consumers  # noqa: E402
import awx.main.models.inventory  # noqa: E402

_noop = lambda *a, **kw: None
awx.main.consumers.emit_channel_notification = _noop
awx.main.models.inventory.emit_channel_notification = _noop

from awx.main.models import Inventory, Organization  # noqa: E402

ORG_NAME = "perf-test-org"


def main():
    org = Organization.objects.get(name=ORG_NAME)
    count = Inventory.objects.filter(organization=org).count()
    start = time.perf_counter()

    if False:
        prof = cProfile.Profile()
        prof.enable()
        Inventory.objects.create(name=f"perf-inventory-{count}", organization=org)
        prof.disable()
        prof.dump_stats("profile.out")
        print("Profile data written to profile.out")
    else:
        Inventory.objects.create(name=f"perf-inventory-{count}", organization=org)

    elapsed = time.perf_counter() - start
    print(f"Created inventory perf-inventory-{count} in {elapsed:.4f}s")


if __name__ == "__main__":
    main()
