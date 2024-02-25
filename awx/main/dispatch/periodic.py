import logging
import time
import yaml
from datetime import datetime


logger = logging.getLogger('awx.main.dispatch.periodic')


class ScheduledTask:
    """
    Class representing schedules, very loosely modeled after python schedule library Job
    the idea of this class is to:
     - only deal in relative times (time since the scheduler global start)
     - only deal in integer math for target runtimes, but float for current relative time

    Missed schedule policy:
    Invariant target times are maintained, meaning that if interval=10s offset=0
    and it runs at t=7s, then it calls for next run in 3s.
    However, if a complete interval has passed, that is counted as a missed run,
    and missed runs are abandoned (no catch-up runs).
    """

    def __init__(self, name: str, data: dict):
        # parameters need for schedule computation
        self.interval = int(data['schedule'].total_seconds())
        self.offset = 0  # offset relative to start time this schedule begins
        self.index = 0  # number of periods of the schedule that has passed

        # parameters that do not affect scheduling logic
        self.last_run = None  # time of last run, only used for debug
        self.completed_runs = 0  # number of times schedule is known to run
        self.name = name
        self.data = data  # used by caller to know what to run

    @property
    def next_run(self):
        "Time until the next run with t=0 being the global_start of the scheduler class"
        return (self.index + 1) * self.interval + self.offset

    def due_to_run(self, relative_time):
        return bool(self.next_run <= relative_time)

    def expected_runs(self, relative_time):
        return int((relative_time - self.offset) / self.interval)

    def mark_run(self, relative_time):
        self.last_run = relative_time
        self.completed_runs += 1
        new_index = self.expected_runs(relative_time)
        if new_index > self.index + 1:
            logger.warning(f'Missed {new_index - self.index - 1} schedules of {self.name}')
        self.index = new_index

    def missed_runs(self, relative_time):
        "Number of times job was supposed to ran but failed to, only used for debug"
        missed_ct = self.expected_runs(relative_time) - self.completed_runs
        # if this is currently due to run do not count that as a missed run
        if missed_ct and self.due_to_run(relative_time):
            missed_ct -= 1
        return missed_ct


class Scheduler:
    def __init__(self, schedule):
        """
        Expects schedule in the form of a dictionary like
        {
            'job1': {'schedule': timedelta(seconds=50), 'other': 'stuff'}
        }
        Only the schedule nearest-second value is used for scheduling,
        the rest of the data is for use by the caller to know what to run.
        """
        self.jobs = [ScheduledTask(name, data) for name, data in schedule.items()]
        min_interval = min(job.interval for job in self.jobs)
        num_jobs = len(self.jobs)

        # this is intentionally oppioniated against spammy schedules
        # a core goal is to spread out the scheduled tasks (for worker management)
        # and high-frequency schedules just do not work with that
        if num_jobs > min_interval:
            raise RuntimeError(f'Number of schedules ({num_jobs}) is more than the shortest schedule interval ({min_interval} seconds).')

        # even space out jobs over the base interval
        for i, job in enumerate(self.jobs):
            job.offset = (i * min_interval) // num_jobs

        # internally times are all referenced relative to startup time, add grace period
        self.global_start = time.time() + 2.0

    def get_and_mark_pending(self):
        relative_time = time.time() - self.global_start
        to_run = []
        for job in self.jobs:
            if job.due_to_run(relative_time):
                to_run.append(job)
                logger.debug(f'scheduler found {job.name} to run, {relative_time - job.next_run} seconds after target')
                job.mark_run(relative_time)
        return to_run

    def time_until_next_run(self):
        relative_time = time.time() - self.global_start
        next_job = min(self.jobs, key=lambda j: j.next_run)
        delta = next_job.next_run - relative_time
        if delta <= 0.1:
            # careful not to give 0 or negative values to the select timeout, which has unclear interpretation
            logger.warning(f'Scheduler next run of {next_job.name} is {-delta} seconds in the past')
            return 0.1
        elif delta > 20.0:
            logger.warning(f'Scheduler next run unexpectedly over 20 seconds in future: {delta}')
            return 20.0
        logger.debug(f'Scheduler next run is {next_job.name} in {delta} seconds')
        return delta

    def debug(self, *args, **kwargs):
        data = dict()
        data['title'] = 'Scheduler status'

        now = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S UTC')
        start_time = datetime.fromtimestamp(self.global_start).strftime('%Y-%m-%d %H:%M:%S UTC')
        relative_time = time.time() - self.global_start
        data['started_time'] = start_time
        data['current_time'] = now
        data['current_time_relative'] = round(relative_time, 3)
        data['total_schedules'] = len(self.jobs)

        data['schedule_list'] = dict(
            [
                (
                    job.name,
                    dict(
                        last_run_seconds_ago=round(relative_time - job.last_run, 3) if job.last_run else None,
                        next_run_in_seconds=round(job.next_run - relative_time, 3),
                        offset_in_seconds=job.offset,
                        completed_runs=job.completed_runs,
                        missed_runs=job.missed_runs(relative_time),
                    ),
                )
                for job in sorted(self.jobs, key=lambda job: job.interval)
            ]
        )
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)
