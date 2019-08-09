from datetime import datetime
from dateutil import rrule

from awxkit.utils import to_ical


class RRule(rrule.rrule):

    @property
    def next_run(self):
        after = self.after(datetime.utcnow())
        if after is None:
            return after
        return after.isoformat() + 'Z'

    def next_runs(self, count=1):
        return [a.isoformat() + 'Z' for a in self.xafter(datetime.utcnow(),
                                                         count=count)]

    def __str__(self):
        dstart = 'DTSTART:{}'.format(to_ical(self._dtstart))
        rules = []
        if self._freq not in range(len(rrule.FREQNAMES)):
            raise Exception('Invalid freq "{}"'.format(self._freq))
        rules.append('FREQ=' + rrule.FREQNAMES[self._freq])

        for name, value in [('INTERVAL', self._interval),
                            ('WKST', self._wkst),
                            ('COUNT', self._count)]:
            if value is not None:
                if name == 'WKST':
                    value = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU'][value]
                rules.append('{}={}'.format(name, value))

        if self._until:
            rules.append('UNTIL={}'.format(to_ical(self._until)))

        for name, value in [('BYSETPOS', self._bysetpos),
                            ('BYMONTH', self._bymonth),
                            ('BYMONTHDAY', self._bymonthday),
                            ('BYYEARDAY', self._byyearday),
                            ('BYWEEKNO', self._byweekno),
                            ('BYWEEKDAY', self._byweekday),
                            ('BYHOUR', self._byhour),
                            ('BYMINUTE', self._byminute),
                            ('BYSECOND', self._bysecond), ]:
            if name == "BYWEEKDAY" and value:
                value = (rrule.weekdays[num] for num in value)
            if value:
                rules.append(name + '=' + ','.join(str(v) for v in value))

        return '{0} RRULE:{1}'.format(dstart, ';'.join(rules))

    __repr__ = __str__
