import React from 'react';
import { act } from 'react-dom/test-utils';
import { RRule } from 'rrule';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { SchedulesAPI } from '../../../api';
import ScheduleAdd from './ScheduleAdd';

jest.mock('../../../api/models/Schedules');

SchedulesAPI.readZoneInfo.mockResolvedValue({
  data: [
    {
      name: 'America/New_York',
    },
  ],
});

let wrapper;

const createSchedule = jest.fn().mockImplementation(() => {
  return {
    data: {
      id: 1,
    },
  };
});

describe('<ScheduleAdd />', () => {
  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ScheduleAdd createSchedule={createSchedule} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });
  afterEach(() => {
    jest.clearAllMocks();
  });
  test('Successfully creates a schedule with repeat frequency: None (run once)', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'none',
        interval: 1,
        name: 'Run once schedule',
        startDateTime: '2020-03-25T10:00:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run once schedule',
      rrule:
        'DTSTART;TZID=America/New_York:20200325T100000 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
    });
  });
  test('Successfully creates a schedule with 10 minute repeat frequency after 10 occurrences', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'after',
        frequency: 'minute',
        interval: 10,
        name: 'Run every 10 minutes 10 times',
        occurrences: 10,
        startDateTime: '2020-03-25T10:30:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run every 10 minutes 10 times',
      rrule:
        'DTSTART;TZID=America/New_York:20200325T103000 RRULE:INTERVAL=10;FREQ=MINUTELY;COUNT=10',
    });
  });
  test('Successfully creates a schedule with hourly repeat frequency ending on a specific date/time', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'onDate',
        endDateTime: '2020-03-26T10:45:00',
        frequency: 'hour',
        interval: 1,
        name: 'Run every hour until date',
        startDateTime: '2020-03-25T10:45:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run every hour until date',
      rrule:
        'DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=HOURLY;UNTIL=20200326T104500',
    });
  });
  test('Successfully creates a schedule with daily repeat frequency', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'day',
        interval: 1,
        name: 'Run daily',
        startDateTime: '2020-03-25T10:45:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run daily',
      rrule:
        'DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=DAILY',
    });
  });
  test('Successfully creates a schedule with weekly repeat frequency on mon/wed/fri', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        daysOfWeek: [RRule.MO, RRule.WE, RRule.FR],
        description: 'test description',
        end: 'never',
        frequency: 'week',
        interval: 1,
        name: 'Run weekly on mon/wed/fri',
        occurrences: 1,
        startDateTime: '2020-03-25T10:45:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run weekly on mon/wed/fri',
      rrule: `DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=${RRule.MO},${RRule.WE},${RRule.FR}`,
    });
  });
  test('Successfully creates a schedule with monthly repeat frequency on the first day of the month', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'month',
        interval: 1,
        name: 'Run on the first day of the month',
        occurrences: 1,
        runOn: 'day',
        runOnDayNumber: 1,
        startDateTime: '2020-04-01T10:45',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run on the first day of the month',
      rrule:
        'DTSTART;TZID=America/New_York:20200401T104500 RRULE:INTERVAL=1;FREQ=MONTHLY;BYMONTHDAY=1',
    });
  });
  test('Successfully creates a schedule with monthly repeat frequency on the last tuesday of the month', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        endDateTime: '2020-03-26T11:00:00',
        frequency: 'month',
        interval: 1,
        name: 'Run monthly on the last Tuesday',
        occurrences: 1,
        runOn: 'the',
        runOnTheDay: 'tuesday',
        runOnTheOccurrence: -1,
        startDateTime: '2020-03-31T11:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Run monthly on the last Tuesday',
      rrule:
        'DTSTART;TZID=America/New_York:20200331T110000 RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=-1;BYDAY=TU',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the first day of March', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'year',
        interval: 1,
        name: 'Yearly on the first day of March',
        occurrences: 1,
        runOn: 'day',
        runOnDayMonth: 3,
        runOnDayNumber: 1,
        startDateTime: '2020-03-01T00:00',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Yearly on the first day of March',
      rrule:
        'DTSTART;TZID=America/New_York:20200301T000000 RRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=1',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the second Friday in April', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'year',
        interval: 1,
        name: 'Yearly on the second Friday in April',
        occurrences: 1,
        runOn: 'the',
        runOnTheOccurrence: 2,
        runOnTheDay: 'friday',
        runOnTheMonth: 4,
        startDateTime: '2020-04-10T11:15',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Yearly on the second Friday in April',
      rrule:
        'DTSTART;TZID=America/New_York:20200410T111500 RRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=2;BYDAY=FR;BYMONTH=4',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the first weekday in October', async () => {
    await act(async () => {
      wrapper.find('ScheduleForm').invoke('handleSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'year',
        interval: 1,
        name: 'Yearly on the first weekday in October',
        occurrences: 1,
        runOn: 'the',
        runOnTheOccurrence: 1,
        runOnTheDay: 'weekday',
        runOnTheMonth: 10,
        startDateTime: '2020-04-10T11:15',
        timezone: 'America/New_York',
      });
    });
    expect(createSchedule).toHaveBeenCalledWith({
      description: 'test description',
      name: 'Yearly on the first weekday in October',
      rrule:
        'DTSTART;TZID=America/New_York:20200410T111500 RRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=1;BYDAY=MO,TU,WE,TH,FR;BYMONTH=10',
    });
  });
});
