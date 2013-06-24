"""
django_extensions.management.jobs
"""

import os
from imp import find_module

_jobs = None


def noneimplementation(meth):
    return None


class JobError(Exception):
    pass


class BaseJob(object):
    help = "undefined job description."
    when = None

    def execute(self):
        raise NotImplementedError("Job needs to implement the execute method")


class MinutelyJob(BaseJob):
    when = "minutely"


class QuarterHourlyJob(BaseJob):
    when = "quarter_hourly"


class HourlyJob(BaseJob):
    when = "hourly"


class DailyJob(BaseJob):
    when = "daily"


class WeeklyJob(BaseJob):
    when = "weekly"


class MonthlyJob(BaseJob):
    when = "monthly"


class YearlyJob(BaseJob):
    when = "yearly"


def my_import(name):
    imp = __import__(name)
    mods = name.split('.')
    if len(mods) > 1:
        for mod in mods[1:]:
            imp = getattr(imp, mod)
    return imp


def find_jobs(jobs_dir):
    try:
        return [f[:-3] for f in os.listdir(jobs_dir) if not f.startswith('_') and f.endswith(".py")]
    except OSError:
        return []


def find_job_module(app_name, when=None):
    parts = app_name.split('.')
    parts.append('jobs')
    if when:
        parts.append(when)
    parts.reverse()
    path = None
    while parts:
        part = parts.pop()
        f, path, descr = find_module(part, path and [path] or None)
    return path


def import_job(app_name, name, when=None):
    jobmodule = "%s.jobs.%s%s" % (app_name, when and "%s." % when or "", name)
    job_mod = my_import(jobmodule)
    # todo: more friendly message for AttributeError if job_mod does not exist
    try:
        job = job_mod.Job
    except:
        raise JobError("Job module %s does not contain class instance named 'Job'" % jobmodule)
    if when and not (job.when == when or job.when is None):
        raise JobError("Job %s is not a %s job." % (jobmodule, when))
    return job


def get_jobs(when=None, only_scheduled=False):
    """
    Returns a dictionary mapping of job names together with their respective
    application class.
    """
    # FIXME: HACK: make sure the project dir is on the path when executed as ./manage.py
    import sys
    try:
        cpath = os.path.dirname(os.path.realpath(sys.argv[0]))
        ppath = os.path.dirname(cpath)
        if ppath not in sys.path:
            sys.path.append(ppath)
    except:
        pass
    _jobs = {}
    if True:
        from django.conf import settings
        for app_name in settings.INSTALLED_APPS:
            scandirs = (None, 'minutely', 'quarter_hourly', 'hourly', 'daily', 'weekly', 'monthly', 'yearly')
            if when:
                scandirs = None, when
            for subdir in scandirs:
                try:
                    path = find_job_module(app_name, subdir)
                    for name in find_jobs(path):
                        if (app_name, name) in _jobs:
                            raise JobError("Duplicate job %s" % name)
                        job = import_job(app_name, name, subdir)
                        if only_scheduled and job.when is None:
                            # only include jobs which are scheduled
                            continue
                        if when and job.when != when:
                            # generic job not in same schedule
                            continue
                        _jobs[(app_name, name)] = job
                except ImportError:
                    # No job module -- continue scanning
                    pass
    return _jobs


def get_job(app_name, job_name):
    jobs = get_jobs()
    if app_name:
        return jobs[(app_name, job_name)]
    else:
        for a, j in jobs.keys():
            if j == job_name:
                return jobs[(a, j)]
        raise KeyError("Job not found: %s" % job_name)


def print_jobs(when=None, only_scheduled=False, show_when=True, show_appname=False, show_header=True):
    jobmap = get_jobs(when, only_scheduled=only_scheduled)
    print("Job List: %i jobs" % len(jobmap))
    jlist = jobmap.keys()
    jlist.sort()
    appname_spacer = "%%-%is" % max(len(e[0]) for e in jlist)
    name_spacer = "%%-%is" % max(len(e[1]) for e in jlist)
    when_spacer = "%%-%is" % max(len(e.when) for e in jobmap.values() if e.when)
    if show_header:
        line = " "
        if show_appname:
            line += appname_spacer % "appname" + " - "
        line += name_spacer % "jobname"
        if show_when:
            line += " - " + when_spacer % "when"
        line += " - help"
        print(line)
        print("-" * 80)

    for app_name, job_name in jlist:
        job = jobmap[(app_name, job_name)]
        line = " "
        if show_appname:
            line += appname_spacer % app_name + " - "
        line += name_spacer % job_name
        if show_when:
            line += " - " + when_spacer % (job.when and job.when or "")
        line += " - " + job.help
        print(line)
