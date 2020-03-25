import {
  dateToInputDateTime,
  getDaysInMonth,
  getDayString,
  getMonthString,
  getWeekNumber,
  getWeekString,
  formatDateString,
  formatDateStringUTC,
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

describe('getDaysInMonth', () => {
  test('it returns the expected value', () => {
    expect(getDaysInMonth('2020-02-15T00:00:00Z')).toEqual(29);
    expect(getDaysInMonth('2020-03-15T00:00:00Z')).toEqual(31);
    expect(getDaysInMonth('2020-04-15T00:00:00Z')).toEqual(30);
  });
});

describe('getWeekNumber', () => {
  test('it returns the expected value', () => {
    expect(getWeekNumber('2020-02-01T00:00:00Z')).toEqual(1);
    expect(getWeekNumber('2020-02-08T00:00:00Z')).toEqual(2);
    expect(getWeekNumber('2020-02-15T00:00:00Z')).toEqual(3);
    expect(getWeekNumber('2020-02-22T00:00:00Z')).toEqual(4);
    expect(getWeekNumber('2020-02-29T00:00:00Z')).toEqual(5);
  });
});

describe('getDayString', () => {
  test('it returns the expected value', () => {
    expect(getDayString(0, i18n)).toEqual('Sunday');
    expect(getDayString(1, i18n)).toEqual('Monday');
    expect(getDayString(2, i18n)).toEqual('Tuesday');
    expect(getDayString(3, i18n)).toEqual('Wednesday');
    expect(getDayString(4, i18n)).toEqual('Thursday');
    expect(getDayString(5, i18n)).toEqual('Friday');
    expect(getDayString(6, i18n)).toEqual('Saturday');
    expect(() => getDayString(7, i18n)).toThrow();
  });
});

describe('getWeekString', () => {
  test('it returns the expected value', () => {
    expect(() => getWeekString(0, i18n)).toThrow();
    expect(getWeekString(1, i18n)).toEqual('first');
    expect(getWeekString(2, i18n)).toEqual('second');
    expect(getWeekString(3, i18n)).toEqual('third');
    expect(getWeekString(4, i18n)).toEqual('fourth');
    expect(getWeekString(5, i18n)).toEqual('fifth');
    expect(() => getWeekString(6, i18n)).toThrow();
  });
});

describe('getMonthString', () => {
  test('it returns the expected value', () => {
    expect(getMonthString(0, i18n)).toEqual('January');
    expect(getMonthString(1, i18n)).toEqual('February');
    expect(getMonthString(2, i18n)).toEqual('March');
    expect(getMonthString(3, i18n)).toEqual('April');
    expect(getMonthString(4, i18n)).toEqual('May');
    expect(getMonthString(5, i18n)).toEqual('June');
    expect(getMonthString(6, i18n)).toEqual('July');
    expect(getMonthString(7, i18n)).toEqual('August');
    expect(getMonthString(8, i18n)).toEqual('September');
    expect(getMonthString(9, i18n)).toEqual('October');
    expect(getMonthString(10, i18n)).toEqual('November');
    expect(getMonthString(11, i18n)).toEqual('December');
    expect(() => getMonthString(12, i18n)).toThrow();
  });
});
