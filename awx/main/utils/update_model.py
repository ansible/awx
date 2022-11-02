from django.db import transaction, DatabaseError, InterfaceError
from django.core.exceptions import ObjectDoesNotExist

import logging
import time

from awx.main.tasks.signals import signal_callback


logger = logging.getLogger('awx.main.tasks.utils')


def update_model(model, pk, _attempt=0, _max_attempts=5, select_for_update=False, **updates):
    """Reload the model instance from the database and update the
    given fields.
    """
    try:
        with transaction.atomic():
            # Retrieve the model instance.
            if select_for_update:
                instance = model.objects.select_for_update().get(pk=pk)
            else:
                instance = model.objects.get(pk=pk)

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
            return update_model(model, pk, _attempt=_attempt + 1, _max_attempts=_max_attempts, **updates)
        else:
            logger.warning(f'Failed to update {model._meta.object_name} pk={pk} after {_attempt} retries.')
            raise
