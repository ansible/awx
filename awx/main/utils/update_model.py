from django.db import transaction, DatabaseError, InterfaceError
from django.core.exceptions import ObjectDoesNotExist

import logging
import time

from awx.main.tasks.signals import signal_callback

logger = logging.getLogger('awx.main.tasks.utils')


class NotOwner(Exception):
    """The job is now owned by another task, so this task may not write it."""

    def __init__(self, pk, owner_task_id, current_task_id):
        self.pk = pk
        self.owner_task_id = owner_task_id
        self.current_task_id = current_task_id
        super().__init__(f'pk={pk} is owned by task {current_task_id!r}, not {owner_task_id!r}')


def _write_fields(model, pk, select_for_update, owner_task_id, updates, required_status=None):
    """Load the row, check ownership and status, and save the given fields in one transaction.

    Both checks run inside the select_for_update transaction, so check and write are atomic.
    They guard different things, and a final status write needs both:

    owner_task_id decides who may write. A claim for adoption replaces celery_task_id, so the
    task that owned the job before is refused with NotOwner.

    required_status makes the write happen once. When set, nothing is written and None is
    returned if the row's current status differs. A reap ends a job without taking ownership,
    so only this check stops the owner from writing a second terminal status over it.
    """
    with transaction.atomic():
        # Retrieve the model instance.
        if select_for_update:
            instance = model.objects.select_for_update().get(pk=pk)
        else:
            instance = model.objects.get(pk=pk)

        if owner_task_id and instance.celery_task_id != owner_task_id:
            raise NotOwner(pk, owner_task_id, instance.celery_task_id)

        if required_status is not None and instance.status != required_status:
            return None

        # Update the appropriate fields and save the model
        # instance, then return the new instance.
        if updates:
            update_fields = ['modified']
            for field, value in updates.items():
                setattr(instance, field, value)
                update_fields.append(field)
                if field == 'status':
                    update_fields.append('failed')
            instance.save(update_fields=update_fields)
        return instance


def _wait_before_retry(pk):
    """Sleep five seconds before a retry, giving up early on an abort signal."""
    for i in range(5):
        time.sleep(1)
        if signal_callback():
            raise RuntimeError(f'Could not fetch {pk} because of receiving abort signal')


def update_model(model, pk, _attempt=0, _max_attempts=5, select_for_update=False, owner_task_id=None, _required_status=None, **updates):
    """Reload the model instance from the database and update the
    given fields.

    With owner_task_id, the row is locked and updated only while its celery_task_id
    still equals owner_task_id; otherwise NotOwner is raised and nothing is written.

    _required_status: when set, the update is skipped and None is returned if the row's
    current status does not match.
    """
    if owner_task_id:
        select_for_update = True
    try:
        return _write_fields(model, pk, select_for_update, owner_task_id, updates, required_status=_required_status)
    except ObjectDoesNotExist:
        return None
    except (DatabaseError, InterfaceError) as e:
        # Log out the error to the debug logger.
        logger.debug('Database error updating %s, retrying in 5 seconds (retry #%d): %s', model._meta.object_name, _attempt + 1, e)

        # Attempt to retry the update, assuming we haven't already
        # tried too many times.
        if _attempt >= _max_attempts:
            logger.warning(f'Failed to update {model._meta.object_name} pk={pk} after {_attempt} retries.')
            raise
        _wait_before_retry(pk)
        return update_model(
            model,
            pk,
            _attempt=_attempt + 1,
            _max_attempts=_max_attempts,
            select_for_update=select_for_update,
            owner_task_id=owner_task_id,
            _required_status=_required_status,
            **updates,
        )
