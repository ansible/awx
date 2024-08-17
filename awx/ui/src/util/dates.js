/* eslint-disable import/prefer-default-export */
import { t } from '@lingui/macro';
import { RRule } from 'rrule';
import { DateTime, Duration } from 'luxon';

const default_config = {
  datetime_format: 'am-pm',
};

const getFormat = (config) =>
  config.datetime_format || default_config.datetime_format;

export function makeDateTime(date, time, tz = null, config = default_config) {
  const formats = {
    'am-pm': 'yyyy-MM-dd h:mm a',
    '24-hour': 'yyyy-LL-dd HH:mm',
  };

  return DateTime.fromFormat(`${date} ${time}`, formats[getFormat(config)], {
    zone: tz,
  });
}

export function formatDateString(dateObj, tz = null, config = default_config) {
  if (dateObj === null) {
    return null;
  }

  if (getFormat(config) === 'am-pm') {
    return tz !== null
      ? DateTime.fromISO(dateObj, { zone: tz }).toLocaleString(
          DateTime.DATETIME_SHORT_WITH_SECONDS
        )
      : DateTime.fromISO(dateObj).toLocaleString(
          DateTime.DATETIME_SHORT_WITH_SECONDS
        );
  }
  if (getFormat(config) === '24-hour') {
    const fmt = 'yyyy-LL-dd, HH:mm:ss';
    return tz !== null
      ? DateTime.fromISO(dateObj, { zone: tz }).toFormat(fmt)
      : DateTime.fromISO(dateObj).toFormat(fmt);
  }
  return null;
}

export function secondsToHHMMSS(seconds) {
  return Duration.fromObject({ seconds }).toFormat('hh:mm:ss');
}

export function secondsToDays(seconds) {
  return Duration.fromObject({ seconds }).toFormat('d');
}

export function timeOfDay(config = default_config) {
  const dateTime = DateTime.local();
  const formats = {
    'am-pm': 'hh:mm:ss:ms a',
    '24-hour': 'HH:mm:ss:ms',
  };
  return dateTime.toFormat(formats[getFormat(config)]);
}

export function dateToInputDateTime(dt, tz = null, config = default_config) {
  const formats = {
    'am-pm': 'h:mm a',
    '24-hour': 'HH:mm',
  };
  let dateTime;
  if (tz) {
    dateTime = DateTime.fromISO(dt, { zone: tz });
  } else {
    dateTime = DateTime.fromISO(dt);
  }
  return [
    dateTime.toFormat('yyyy-LL-dd'),
    dateTime.toFormat(formats[getFormat(config)]),
  ];
}

export function getRRuleDayConstants(dayString) {
  switch (dayString) {
    case 'sunday':
      return RRule.SU;
    case 'monday':
      return RRule.MO;
    case 'tuesday':
      return RRule.TU;
    case 'wednesday':
      return RRule.WE;
    case 'thursday':
      return RRule.TH;
    case 'friday':
      return RRule.FR;
    case 'saturday':
      return RRule.SA;
    case 'day':
      return [
        RRule.MO,
        RRule.TU,
        RRule.WE,
        RRule.TH,
        RRule.FR,
        RRule.SA,
        RRule.SU,
      ];
    case 'weekday':
      return [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR];
    case 'weekendDay':
      return [RRule.SA, RRule.SU];
    default:
      throw new Error(t`Unrecognized day string`);
  }
}
