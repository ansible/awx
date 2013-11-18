from __future__ import absolute_import, unicode_literals

from datetime import datetime

from django.utils.translation import ungettext, ugettext as _
from .utils import now

JUST_NOW = _('just now')
SECONDS_AGO = (_('{seconds} second ago'), _('{seconds} seconds ago'))
MINUTES_AGO = (_('{minutes} minute ago'), _('{minutes} minutes ago'))
HOURS_AGO = (_('{hours} hour ago'), _('{hours} hours ago'))
YESTERDAY_AT = _('yesterday at {time}')
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
OLDER_AGO = _('{number} {type} ago')


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
                return _un(MINUTES_AGO, n=minutes).format(minutes=minutes)
            else:
                return JUST_NOW
        else:
            return _un(HOURS_AGO, n=hours).format(hours=hours)

    if delta_midnight.days == 0:
        return YESTERDAY_AT.format(time=date.strftime('%H:%M'))

    count = 0
    for chunk, singular_plural in OLDER_CHUNKS:
        if days >= chunk:
            count = round((delta_midnight.days + 1) / chunk, 0)
            type_ = _un(singular_plural, n=count)
            break

    return OLDER_AGO.format(number=count, type=type_)
