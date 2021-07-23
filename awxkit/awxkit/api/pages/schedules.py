from contextlib import suppress

from awxkit.api.pages import UnifiedJob
from awxkit.api.resources import resources
from awxkit.config import config
import awxkit.exceptions as exc

from . import page
from . import base


class Schedule(UnifiedJob):

    NATURAL_KEY = ('unified_job_template', 'name')

    def silent_delete(self):
        """If we are told to prevent_teardown of schedules, then keep them
        but do not leave them activated, or system will be swamped quickly"""
        try:
            if not config.prevent_teardown:
                return self.delete()
            else:
                self.patch(enabled=False)
        except (exc.NoContent, exc.NotFound, exc.Forbidden):
            pass


page.register_page([resources.schedule, resources.related_schedule], Schedule)


class Schedules(page.PageList, Schedule):
    def get_zoneinfo(self):
        return SchedulesZoneInfo(self.connection).get()

    def preview(self, rrule=''):
        payload = dict(rrule=rrule)
        return SchedulesPreview(self.connection).post(payload)

    def add_credential(self, cred):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=cred.id))

    def remove_credential(self, cred):
        with suppress(exc.NoContent):
            self.related.credentials.post(dict(id=cred.id, disassociate=True))


page.register_page([resources.schedules, resources.related_schedules], Schedules)


class SchedulesPreview(base.Base):

    pass


page.register_page(((resources.schedules_preview, 'post'),), SchedulesPreview)


class SchedulesZoneInfo(base.Base):
    def __getitem__(self, idx):
        return self.json[idx]


page.register_page(((resources.schedules_zoneinfo, 'get'),), SchedulesZoneInfo)
