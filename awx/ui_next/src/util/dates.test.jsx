import { RRule } from 'rrule';
import {
  dateToInputDateTime,
  formatDateString,
  formatDateStringUTC,
  getRRuleDayConstants,
  secondsToHHMMSS,
} from './dates';

const i18n = {
  _: key => {
    if (key.values) {
      Object.entries(key.values).forEach(([k, v]) => {
        key.id = key.id.replace(new RegExp(`\\{${k}\\}`), v);
      });
    }
    return key.id;
  },
};

describe('formatDateString', () => {
  test('it returns the expected value', () => {
    const lang = 'en-US';
    expect(formatDateString('', lang)).toEqual('Invalid Date');
    expect(formatDateString({}, lang)).toEqual('Invalid Date');
    expect(formatDateString(undefined, lang)).toEqual('Invalid Date');
    expect(formatDateString('2018-01-31T01:14:52.969227Z', lang)).toEqual(
      '1/31/2018, 1:14:52 AM'
    );
  });
});

describe('formatDateStringUTC', () => {
  test('it returns the expected value', () => {
    const lang = 'en-US';
    expect(formatDateStringUTC('', lang)).toEqual('Invalid Date');
    expect(formatDateStringUTC({}, lang)).toEqual('Invalid Date');
    expect(formatDateStringUTC(undefined, lang)).toEqual('Invalid Date');
    expect(formatDateStringUTC('2018-01-31T01:14:52.969227Z', lang)).toEqual(
      '1/31/2018, 1:14:52 AM'
    );
  });
});

describe('secondsToHHMMSS', () => {
  test('it returns the expected value', () => {
    expect(secondsToHHMMSS(50000)).toEqual('13:53:20');
  });
});

describe('dateToInputDateTime', () => {
  test('it returns the expected value', () => {
    expect(
      dateToInputDateTime(new Date('2018-01-31T01:14:52.969227Z'))
    ).toEqual('2018-01-31T01:14:52');
  });
});

describe('getRRuleDayConstants', () => {
  test('it returns the expected value', () => {
    expect(getRRuleDayConstants('monday', i18n)).toEqual(RRule.MO);
    expect(getRRuleDayConstants('tuesday', i18n)).toEqual(RRule.TU);
    expect(getRRuleDayConstants('wednesday', i18n)).toEqual(RRule.WE);
    expect(getRRuleDayConstants('thursday', i18n)).toEqual(RRule.TH);
    expect(getRRuleDayConstants('friday', i18n)).toEqual(RRule.FR);
    expect(getRRuleDayConstants('saturday', i18n)).toEqual(RRule.SA);
    expect(getRRuleDayConstants('sunday', i18n)).toEqual(RRule.SU);
    expect(getRRuleDayConstants('day', i18n)).toEqual([
      RRule.MO,
      RRule.TU,
      RRule.WE,
      RRule.TH,
      RRule.FR,
      RRule.SA,
      RRule.SU,
    ]);
    expect(getRRuleDayConstants('weekday', i18n)).toEqual([
      RRule.MO,
      RRule.TU,
      RRule.WE,
      RRule.TH,
      RRule.FR,
    ]);
    expect(getRRuleDayConstants('weekendDay', i18n)).toEqual([
      RRule.SA,
      RRule.SU,
    ]);
    expect(() => getRRuleDayConstants('foobar', i18n)).toThrow();
  });
});
