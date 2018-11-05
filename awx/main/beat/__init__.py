import signal
import logging
from datetime import datetime, timedelta
from functools import partial

from django.conf import settings

from awx.main.dispatch import get_local_queuename

logger = logging.getLogger('awx.main.beat')


class ScheduleEntry(object):
    def __init__(self, name, task, period, expiration, epoch):
        self.name = name
        self.task = task
        self.period = period
        self.periods_missed = 0
        self.expiration = expiration
        self.epoch = epoch
        self.last_exec_absolute = None

    def calc_next_cycle_abs(self, now):
        current_period = int(((now - self.epoch).total_seconds() / self.period.total_seconds())) + 1
        return self.epoch + timedelta(seconds=(current_period * self.period.total_seconds()))

    def record_run(self, now):
        last_exec = self.epoch if self.last_exec_absolute is None else self.last_exec_absolute
        periods_missed = int((now - last_exec).total_seconds() / self.period.total_seconds()) - 1
        if periods_missed > 0:
            logger.warn("{} missed {} periods".format(self, periods_missed))
            self.periods_missed += periods_missed
        self.last_exec_absolute = now

    def should_run(self, now):
        if self.last_exec_absolute is None:
            return True
        current_period = int(((now - self.epoch).total_seconds() / self.period.total_seconds()))
        current_period_begin_abs = self.epoch + timedelta(seconds=current_period * self.period.total_seconds())
        return bool(self.last_exec_absolute < current_period_begin_abs)

    def __repr__(self):
        return ("<name: {}, task: {}, period: {}, expiration: {}, last_exec_absolute: {}>"
                .format(self.name, self.task, self.period, self.expiration, self.last_exec_absolute))


class Scheduler(object):
    def __init__(self, epoch=datetime.utcnow()):
        self.epoch = epoch
        self.entries = []
        self.now = epoch

    def add_entry(self, entry):
        self.entries.append(entry)

    def update_time(self):
        self.now = datetime.utcnow()

    def get_time(self):
        return self.now

    '''
    Should be called at the last possible moment
    '''
    def next_wakeup(self):
        next_entry = self.entries[0]
        next_cycle_smallest = self.entries[0].calc_next_cycle_abs(self.get_time())
        for entry in self.entries:
            next_cycle_tmp = entry.calc_next_cycle_abs(self.get_time())
            if next_cycle_tmp < next_cycle_smallest:
                next_entry = entry
                next_cycle_smallest = next_cycle_tmp

        return next_cycle_smallest

    def get_schedules_to_run(self):
        self.update_time()
        n = self.get_time()
        for t in self.entries:
            if t.should_run(n):
                yield t
                t.record_run(n)


def handler(state, signum, frame):
    state.run_tasks()
    signal.setitimer(signal.ITIMER_REAL, state.next_wakeup_seconds())


class Beat(object):
    def __init__(self, schedules, epoch=datetime.utcnow(), *args, **kwargs):
        self.scheduler = Scheduler(epoch)
        self.scheduler_entry = None

        for k,v in schedules.iteritems():
            self.scheduler.add_entry(ScheduleEntry(k,
                                                   v.get('task', None),
                                                   v.get('schedule', None),
                                                   v.get('options', {}).get('expires', None),
                                                   self.scheduler.epoch))

    def start(self):
        signal.signal(signal.SIGALRM, partial(handler, self))
        self.run_tasks()
        signal.setitimer(signal.ITIMER_REAL, self.next_wakeup_seconds())

        while True:
            self.tick()
            signal.pause()

    def tick(self):
        pass

    def apply_async(self, *args, **kwargs):
        r"""
        overwrite me
        """
        pass

    def next_wakeup_seconds(self):
        self.scheduler.update_time()
        return (self.scheduler.next_wakeup() - self.scheduler.get_time()).total_seconds()

    def run_tasks(self):
        for sched in self.scheduler.get_schedules_to_run():
            self.apply_async(sched, queue=get_local_queuename(),
                             expiration=sched.period.total_seconds())

