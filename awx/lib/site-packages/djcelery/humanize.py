from __future__ import absolute_import

from datetime import datetime

from django.utils.translation import ungettext, ugettext as _
from .utils import now

JUST_NOW = _('just now')
SECONDS_AGO = (_('%(seconds)d second ago'), _('%(seconds)d seconds ago'))
MINUTES_AGO = (_('%(minutes)d minute ago'), _('%(minutes)d minutes ago'))
HOURS_AGO = (_('%(hours)d hour ago'), _('%(hours)d hours ago'))
YESTERDAY_AT = _('yesterday at %(time)s')
OLDER_YEAR = (_('year'), _('years'))
OLDER_MONTH = (_('month'), _('months'))
OLDER_WEEK = (_('week'), _('weeks'))
OLDER_DAY = (_('day'), _('days'))
OLDER_CHUNKS = (
    (365.0, OLDER_YEAR),
    (30.0, OLDER_MONTH),
    (7.0, OLDER_WEEK),
    (1.0, OLDER_DAY),
)
OLDER_AGO = _('%(number)d %(type)s ago')


def _un(singular__plural, n=None):
    singular, plural = singular__plural
    return ungettext(singular, plural, n)


def naturaldate(date):
    """Convert datetime into a human natural date string."""

    if not date:
        return ''

    right_now = now()
    today = datetime(right_now.year, right_now.month,
                     right_now.day, tzinfo=right_now.tzinfo)
    delta = right_now - date
    delta_midnight = today - date

    days = delta.days
    hours = round(delta.seconds / 3600, 0)
    minutes = delta.seconds / 60

    if days < 0:
        return JUST_NOW

    if days == 0:
        if hours == 0:
            if minutes > 0:
                return _un(MINUTES_AGO, n=minutes) % {'minutes': minutes}
            else:
                return JUST_NOW
        else:
            return _un(HOURS_AGO, n=hours) % {'hours': hours}

    if delta_midnight.days == 0:
        return YESTERDAY_AT % {'time': date.strftime('%H:%M')}

    count = 0
    for chunk, singular_plural in OLDER_CHUNKS:
        if days >= chunk:
            count = round((delta_midnight.days + 1) / chunk, 0)
            type_ = _un(singular_plural, n=count)
            break

    return OLDER_AGO % {'number': count, 'type': type_}
