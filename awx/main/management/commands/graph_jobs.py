# Python
import asciichartpy as chart
import collections
import time
import sys

# Django
from django.db.models import Count
from django.core.management.base import BaseCommand

# AWX
from awx.main.models import (
    Job,
    Instance
)


DEFAULT_WIDTH = 100
DEFAULT_HEIGHT = 30


def chart_color_lookup(color_str):
    return getattr(chart, color_str)


def clear_screen():
    print(chr(27) + "[2J")


class JobStatus():
    def __init__(self, status, color, width):
        self.status = status
        self.color = color
        self.color_code = chart_color_lookup(color)
        self.x = collections.deque(maxlen=width)
        self.y = collections.deque(maxlen=width)

    def tick(self, x, y):
        self.x.append(x)
        self.y.append(y)


class JobStatusController:
    RESET = chart_color_lookup('reset')

    def __init__(self, width):
        self.plots = [
            JobStatus('pending', 'red', width),
            JobStatus('waiting', 'blue', width),
            JobStatus('running', 'green', width)
        ]
        self.ts_start = int(time.time())

    def tick(self):
        ts = int(time.time()) - self.ts_start
        q = Job.objects.filter(status__in=['pending','waiting','running']).values_list('status').order_by().annotate(Count('status'))
        status_count = dict(pending=0, waiting=0, running=0)
        for status, count in q:
            status_count[status] = count

        for p in self.plots:
            p.tick(ts, status_count[p.status])

    def series(self):
        return [list(p.y) for p in self.plots]

    def generate_status(self):
        line = ""
        lines = []
        for p in self.plots:
            lines.append(f'{p.color_code}{p.status} {p.y[-1]}{self.RESET}')

        line += ", ".join(lines) + '\n'

        width = 5
        time_running = int(time.time()) - self.ts_start
        instances = Instance.objects.all().order_by('hostname')
        line += "Capacity:  " + ", ".join([f"{instance.capacity:{width}}" for instance in instances]) + '\n'
        line += "Remaining: " + ", ".join([f"{instance.remaining_capacity:{width}}" for instance in instances]) + '\n'
        line += f"Seconds running: {time_running}" + '\n'

        return line


class Command(BaseCommand):
    help = "Plot pending, waiting, running jobs over time on the terminal"

    def add_arguments(self, parser):
        parser.add_argument('--refresh', dest='refresh', type=float, default=1.0,
                            help='Time between refreshes of the graph and data in seconds (defaults to 1.0)')
        parser.add_argument('--width', dest='width', type=int, default=DEFAULT_WIDTH,
                            help=f'Width of the graph (defaults to {DEFAULT_WIDTH})')
        parser.add_argument('--height', dest='height', type=int, default=DEFAULT_HEIGHT,
                            help=f'Height of the graph (defaults to {DEFAULT_HEIGHT})')

    def handle(self, *args, **options):
        refresh_seconds = options['refresh']
        width = options['width']
        height = options['height']

        jctl = JobStatusController(width)

        conf = {
            'colors': [chart_color_lookup(p.color) for p in jctl.plots],
            'height': height,
        }

        while True:
            jctl.tick()

            draw = chart.plot(jctl.series(), conf)
            status_line = jctl.generate_status()
            clear_screen()
            print(draw)
            sys.stdout.write(status_line)
            time.sleep(refresh_seconds)

