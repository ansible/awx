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


def update_model(model, pk, _attempt=0, _max_attempts=5, select_for_update=False, owner_task_id=None, **updates):
    """Reload the model instance from the database and update the
    given fields.

    With owner_task_id, the row is locked and updated only while its celery_task_id
    still equals owner_task_id; otherwise NotOwner is raised and nothing is written.
    """
    if owner_task_id:
        select_for_update = True
    try:
        with transaction.atomic():
            # Retrieve the model instance.
            if select_for_update:
                instance = model.objects.select_for_update().get(pk=pk)
            else:
                instance = model.objects.get(pk=pk)

            if owner_task_id and instance.celery_task_id != owner_task_id:
                raise NotOwner(pk, owner_task_id, instance.celery_task_id)

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
    except ObjectDoesNotExist:
        return None
    except (DatabaseError, InterfaceError) as e:
        # Log out the error to the debug logger.
        logger.debug('Database error updating %s, retrying in 5 seconds (retry #%d): %s', model._meta.object_name, _attempt + 1, e)

        # Attempt to retry the update, assuming we haven't already
        # tried too many times.
        if _attempt < _max_attempts:
            for i in range(5):
                time.sleep(1)
                if signal_callback():
                    raise RuntimeError(f'Could not fetch {pk} because of receiving abort signal')
            return update_model(
                model, pk, _attempt=_attempt + 1, _max_attempts=_max_attempts, select_for_update=select_for_update, owner_task_id=owner_task_id, **updates
            )
        else:
            logger.warning(f'Failed to update {model._meta.object_name} pk={pk} after {_attempt} retries.')
            raise
