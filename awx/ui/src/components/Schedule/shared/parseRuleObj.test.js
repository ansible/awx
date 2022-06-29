import UnifiedJobTemplates from 'api/models/UnifiedJobTemplates';
import parseRuleObj from './parseRuleObj';
import { DateTime, Settings } from 'luxon';

describe(parseRuleObj, () => {
  let origNow = Settings.now;
  beforeEach(() => {
    const expectedNow = DateTime.local(2022, 6, 1, 13, 0, 0);
    Settings.now = () => expectedNow.toMillis();
  });

  afterEach(() => {
    Settings.now = origNow;
  });

  test('should parse weekly recurring rrule', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=America/New_York:20220608T123000 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=MO',
      dtstart: '2022-06-13T16:30:00Z',
      timezone: 'US/Eastern',
      until: '',
      dtend: null,
    };

    const parsed = parseRuleObj(schedule);

    expect(parsed).toEqual({
      startDate: '2022-06-13',
      startTime: '12:30 PM',
      frequency: ['week'],
      frequencyOptions: {
        week: {
          interval: 1,
          end: 'never',
          occurrences: 1,
          endDate: '2022-06-02',
          endTime: '1:00 PM',
          daysOfWeek: [{ weekday: 0, n: undefined }],
        },
      },
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });

  test('should parse non-recurring rrule', () => {
    const schedule = {
      rrule:
        'DTSTART;TZID=America/New_York:20220610T130000 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
      dtstart: '2022-06-10T17:00:00Z',
      dtend: '2022-06-10T17:00:00Z',
      timezone: 'US/Eastern',
      until: '',
    };

    expect(parseRuleObj(schedule)).toEqual({
      end: 'after',
      startDate: '2022-06-10',
      startTime: '1:00 PM',
      frequency: [],
      frequencyOptions: {},
      exceptionFrequency: [],
      exceptionOptions: {},
    });
  });
});
