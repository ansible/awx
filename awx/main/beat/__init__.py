import signal
from django.conf import settings
from datetime import datetime
from functools import partial


class ScheduleEntry(object):
    def __init__(self, task, period, expiration):
        self.task = task
        self.period = period
        self.expiration = expiration
        self.last_period_absolute = None

    def calc_next_cycle_abs(self, epoch):
        if self.last_period_absolute is None:
            return (epoch + self.period)
        return self.last_period_absolute + self.period

    def update_next_cycle_abs(self, epoch):
        if self.last_period_absolute is None:
            self.last_period_absolute = epoch + self.period
        else:
            self.last_period_absolute += self.period
        return self.last_period_absolute

    def __repr__(self):
        return ("<task: {}, period: {}, expiration: {}, last_period_absolute: {}>"
                .format(self.task, self.period, self.expiration, self.last_period_absolute))


class Scheduler(object):
    def __init__(self):
        self.epoch = datetime.utcnow()
        self.entries = []
        self.current_pending_schedule = None
        self.now = None

    def add_entry(self, entry):
        self.entries.append(entry)

    def update_time(self):
        self.now = datetime.utcnow()

    def get_time(self):
        return self.now

    '''
    Should be called at the last possible moment
    '''
    def next_cycle(self):
        next_entry = self.entries[0]
        next_cycle_smallest = self.entries[0].calc_next_cycle_abs(self.epoch)
        for entry in self.entries:
            next_cycle_tmp = entry.calc_next_cycle_abs(self.epoch)
            if next_cycle_tmp < next_cycle_smallest:
                next_entry = entry
                next_cycle_smallest = next_cycle_tmp

        self.current_pending_schedule = next_entry
        next_entry.update_next_cycle_abs(self.epoch)

        return next_cycle_smallest


def handler(state, signum, frame):
    state.apply_async(state.scheduler_entry, expiration=state.scheduler_entry.period.total_seconds())

    state.scheduler.update_time()
    next_wakeup = state.scheduler.next_cycle() - state.scheduler.get_time()
    state.scheduler_entry = state.scheduler.current_pending_schedule
    next_wakeup_seconds = next_wakeup.total_seconds()
    if next_wakeup_seconds < 0:
        next_wakeup_seconds = .1

    signal.setitimer(signal.ITIMER_REAL, next_wakeup_seconds)


class Beat(object):
    def __init__(self, *args, **kwargs):
        self.scheduler = Scheduler()
        self.scheduler_entry = None

        for k,v in settings.CELERYBEAT_SCHEDULE.iteritems():
            self.scheduler.add_entry(ScheduleEntry(v.get('task', None),
                                                   v.get('schedule', None),
                                                   v.get('options', {}).get('expires', None)))

    def start(self):
        signal.signal(signal.SIGALRM, partial(handler, self))

        self.scheduler.update_time()
        next_wakeup = (self.scheduler.next_cycle() - self.scheduler.get_time())
        next_wakeup_seconds = next_wakeup.total_seconds()
        self.scheduler_entry = self.scheduler.current_pending_schedule
        signal.setitimer(signal.ITIMER_REAL, next_wakeup_seconds)

        while True:
            self.tick()
            signal.pause()

    def tick(self):
        pass

