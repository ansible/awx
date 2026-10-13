"""A clock tests can set and advance, for code that takes a `clock` callable."""

from django.utils.timezone import now, timedelta


class FakeClock:
    def __init__(self, start=None):
        self.current = start or now()

    def __call__(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)
        return self.current
