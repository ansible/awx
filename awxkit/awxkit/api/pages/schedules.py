from awxkit.api.pages import UnifiedJob
from awxkit.api.resources import resources
import awxkit.exceptions as exc
from awxkit.utils import suppress
from . import page
from . import base


class Schedule(UnifiedJob):

    NATURAL_KEY = ('unified_job_template', 'name')


page.register_page([resources.schedule,
                    resources.related_schedule], Schedule)


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


page.register_page([resources.schedules,
                    resources.related_schedules], Schedules)


class SchedulesPreview(base.Base):

    pass


page.register_page(((resources.schedules_preview, 'post'),), SchedulesPreview)


class SchedulesZoneInfo(base.Base):

    def __getitem__(self, idx):
        return self.json[idx]


page.register_page(((resources.schedules_zoneinfo, 'get'),), SchedulesZoneInfo)
