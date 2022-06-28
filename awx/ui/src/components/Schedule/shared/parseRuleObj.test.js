import UnifiedJobTemplates from 'api/models/UnifiedJobTemplates';
import parseRuleObj from './parseRuleObj';

describe(parseRuleObj, () => {
  test('should parse recurring rrule', () => {
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
          daysOfWeek: [{ weekday: 0, n: undefined }],
          end: 'never',
        },
      },
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
    });
  });
});
