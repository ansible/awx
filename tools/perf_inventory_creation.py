#!/usr/bin/env python
import argparse
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

from awx.main.models import Inventory, Organization, User  # noqa: E402

ORG_NAME = "perf-test-org"
USERNAME = "rando"
BATCH_SIZE = 100


def main():
    parser = argparse.ArgumentParser(description="Performance test for inventory creation")
    parser.add_argument("count", nargs="?", type=int, default=1000, help="Number of inventories to create (default: 1000)")
    args = parser.parse_args()
    total_inventories = args.count
    # Delete org if it already exists so the script is re-runnable
    try:
        old_org = Organization.objects.get(name=ORG_NAME)
        print(f"Deleting existing organization '{ORG_NAME}' (id={old_org.id})...")
        old_org.delete()
    except Organization.DoesNotExist:
        pass

    org = Organization.objects.create(name=ORG_NAME)
    print(f"Created organization '{ORG_NAME}' (id={org.id})")

    user, created = User.objects.get_or_create(username=USERNAME)
    if created:
        user.set_password(USERNAME)
        user.save()
        print(f"Created user '{USERNAME}'")
    else:
        print(f"User '{USERNAME}' already exists")

    org.admin_role.members.add(user)
    print(f"Granted organization admin to '{USERNAME}'")

    print(f"\nCreating {total_inventories} inventories in batches of {BATCH_SIZE}...\n")

    print("batch inventory_start inventory_end avg_time max_time")
    for batch_start in range(0, total_inventories, BATCH_SIZE):
        batch_times = []
        for i in range(batch_start, batch_start + BATCH_SIZE):
            start = time.perf_counter()
            Inventory.objects.create(name=f"perf-inventory-{i}", organization=org)
            elapsed = time.perf_counter() - start
            batch_times.append(elapsed)

        batch_num = (batch_start // BATCH_SIZE) + 1
        avg_time = sum(batch_times) / len(batch_times)
        max_time = max(batch_times)
        print(f"{batch_num} {batch_start} {batch_start + BATCH_SIZE - 1} {avg_time:.4f} {max_time:.4f}")

    total_count = Inventory.objects.filter(organization=org).count()
    print(f"\nDone. Total inventories in org: {total_count}")


if __name__ == "__main__":
    main()
