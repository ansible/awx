import cProfile
import functools
import pstats
import os
import uuid
import datetime
import json
import sys


class AWXProfileBase:
    def __init__(self, name, dest):
        self.name = name
        self.dest = dest
        self.results = {}

    def generate_results(self):
        raise RuntimeError("define me")

    def output_results(self, fname=None):
        if not os.path.isdir(self.dest):
            os.makedirs(self.dest)

        if fname:
            fpath = os.path.join(self.dest, fname)
            with open(fpath, 'w') as f:
                f.write(json.dumps(self.results, indent=2))


class AWXTiming(AWXProfileBase):
    def __init__(self, name, dest='/var/log/tower/timing'):
        super().__init__(name, dest)

        self.time_start = None
        self.time_end = None

    def start(self):
        self.time_start = datetime.datetime.now()

    def stop(self):
        self.time_end = datetime.datetime.now()

        self.generate_results()
        self.output_results()

    def generate_results(self):
        diff = (self.time_end - self.time_start).total_seconds()
        self.results = {
            'name': self.name,
            'diff': f'{diff}-seconds',
        }

    def output_results(self):
        fname = f"{self.results['diff']}-{self.name}-{uuid.uuid4()}.time"
        super().output_results(fname)


def timing(name, *init_args, **init_kwargs):
    def decorator_profile(func):
        @functools.wraps(func)
        def wrapper_profile(*args, **kwargs):
            timing = AWXTiming(name, *init_args, **init_kwargs)
            timing.start()
            res = func(*args, **kwargs)
            timing.stop()
            return res
        return wrapper_profile
    return decorator_profile


class AWXProfiler(AWXProfileBase):
    def __init__(self, name, dest='/var/log/tower/profile', dot_enabled=True):
        '''
        Try to do as little as possible in init. Instead, do the init
        only when the profiling is started.
        '''
        super().__init__(name, dest)
        self.started = False
        self.dot_enabled = dot_enabled
        self.results = {
            'total_time_seconds': 0,
        }

    def generate_results(self):
        self.results['total_time_seconds'] = pstats.Stats(self.prof).total_tt

    def output_results(self):
        super().output_results()

        filename_base = '%.3fs-%s-%s-%s' % (self.results['total_time_seconds'], self.name, self.pid, uuid.uuid4())
        pstats_filepath = os.path.join(self.dest, f"{filename_base}.pstats")
        extra_data = ""

        if self.dot_enabled:
            try:
                from gprof2dot import main as generate_dot
            except ImportError:
                extra_data = 'Dot graph generation failed due to package "gprof2dot" being unavailable.'
            else:
                raw_filepath = os.path.join(self.dest, f"{filename_base}.raw")
                dot_filepath = os.path.join(self.dest, f"{filename_base}.dot")

                pstats.Stats(self.prof).dump_stats(raw_filepath)
                generate_dot([
                    '-n', '2.5', '-f', 'pstats', '-o',
                    dot_filepath,
                    raw_filepath
                ])
                os.remove(raw_filepath)

        with open(pstats_filepath, 'w') as f:
            print(f"{self.name}, {extra_data}", file=f)
            pstats.Stats(self.prof, stream=f).sort_stats('cumulative').print_stats()
        return pstats_filepath


    def start(self):
        self.prof = cProfile.Profile()
        self.pid = os.getpid()

        self.prof.enable()
        self.started = True

    def is_started(self):
        return self.started

    def stop(self):
        if self.started:
            self.prof.disable()

            self.generate_results()
            res = self.output_results()
            self.started = False
            return res
        else:
            print("AWXProfiler::stop() called without calling start() first", file=sys.stderr)
            return None


def profile(name, *init_args, **init_kwargs):
    def decorator_profile(func):
        @functools.wraps(func)
        def wrapper_profile(*args, **kwargs):
            prof = AWXProfiler(name, *init_args, **init_kwargs)
            prof.start()
            res = func(*args, **kwargs)
            prof.stop()
            return res
        return wrapper_profile
    return decorator_profile

