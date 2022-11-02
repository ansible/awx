import React from 'react';
import { act } from 'react-dom/test-utils';
import { RRule } from 'rrule';
import {
  SchedulesAPI,
  InventoriesAPI,
  CredentialsAPI,
  CredentialTypesAPI,
} from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ScheduleEdit from './ScheduleEdit';

jest.mock('../../../api');

let wrapper;
const mockSchedule = {
  rrule:
    'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
  id: 27,
  type: 'schedule',
  url: '/api/v2/schedules/27/',
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
    },
    inventory: { id: 702, name: 'Inventory' },
  },
  created: '2020-04-02T18:43:12.664142Z',
  modified: '2020-04-02T18:43:12.664185Z',
  name: 'mock schedule',
  description: '',
  extra_data: {},
  inventory: 1,
  scm_branch: null,
  job_type: null,
  job_tags: null,
  skip_tags: null,
  limit: null,
  diff_mode: null,
  verbosity: null,
  unified_job_template: 11,
  enabled: true,
  dtstart: '2020-04-02T18:45:00Z',
  dtend: '2020-04-02T18:45:00Z',
  next_run: '2020-04-02T18:45:00Z',
  timezone: 'America/New_York',
  until: '',
};

describe('<ScheduleEdit />', () => {
  beforeEach(async () => {
    SchedulesAPI.readZoneInfo.mockResolvedValue({
      data: [
        {
          name: 'America/New_York',
        },
      ],
    });

    SchedulesAPI.readCredentials.mockResolvedValue({
      data: {
        results: [
          {
            name: 'schedule credential 1',
            id: 1,
            kind: 'vault',
            credential_type: 3,
            inputs: {},
          },
          {
            name: 'schedule credential 2',
            id: 2,
            kind: 'aws',
            credential_type: 4,
            inputs: {},
          },
        ],
        count: 2,
      },
    });

    CredentialTypesAPI.loadAllTypes.mockResolvedValue([
      { id: 1, name: 'ssh', kind: 'ssh' },
    ]);

    CredentialsAPI.read.mockResolvedValue({
      data: {
        count: 3,
        results: [
          {
            id: 1,
            name: 'Credential 1',
            kind: 'ssh',
            url: '',
            credential_type: 1,
          },
          {
            id: 2,
            name: 'Credential 2',
            kind: 'ssh',
            url: '',
            credential_type: 1,
          },
          {
            id: 3,
            name: 'Credential 3',
            kind: 'ssh',
            url: '',
            credential_type: 1,
          },
        ],
      },
    });

    CredentialsAPI.readOptions.mockResolvedValue({
      data: {
        related_search_fields: [],
        actions: { GET: { filterabled: true } },
      },
    });

    SchedulesAPI.update.mockResolvedValue({
      data: {
        id: 27,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ScheduleEdit
          schedule={mockSchedule}
          resource={{
            id: 700,
            type: 'job_template',
            inventory: 1,
            summary_fields: {
              credentials: [
                { name: 'job template credential', id: 75, kind: 'ssh' },
              ],
            },
            name: 'Foo Job Template',
            description: '',
          }}
          resourceDefaultCredentials={[]}
          launchConfig={{
            can_start_without_user_input: false,
            passwords_needed_to_start: [],
            ask_scm_branch_on_launch: false,
            ask_variables_on_launch: false,
            ask_tags_on_launch: false,
            ask_diff_mode_on_launch: false,
            ask_skip_tags_on_launch: false,
            ask_job_type_on_launch: false,
            ask_limit_on_launch: false,
            ask_verbosity_on_launch: false,
            ask_inventory_on_launch: true,
            ask_credential_on_launch: true,
            survey_enabled: false,
            variables_needed_to_start: [],
            credential_needed_to_start: true,
            inventory_needed_to_start: true,
            job_template_data: {
              name: 'Demo Job Template',
              id: 7,
              description: '',
            },
            defaults: {
              extra_vars: '---',
              diff_mode: false,
              limit: '',
              job_tags: '',
              skip_tags: '',
              job_type: 'run',
              verbosity: 0,
              inventory: {
                name: null,
                id: null,
              },
              scm_branch: '',
              credentials: [],
            },
          }}
          surveyConfig={{}}
        />
      );
    });
    wrapper.update();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Successfully creates a schedule with repeat frequency: None (run once)', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: [],
        name: 'Run once schedule',
        startDate: '2020-03-25',
        startTime: '10:00 AM',
        timezone: 'America/New_York',
      });
    });

    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run once schedule',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200325T100000 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
    });
  });

  test('Successfully creates a schedule with 10 minute repeat frequency after 10 occurrences', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['minute'],
        frequencyOptions: {
          minute: {
            end: 'after',
            interval: 10,
            occurrences: 10,
          },
        },
        name: 'Run every 10 minutes 10 times',
        startDate: '2020-03-25',
        startTime: '10:30 AM',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run every 10 minutes 10 times',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200325T103000 RRULE:INTERVAL=10;FREQ=MINUTELY;COUNT=10',
    });
  });

  test('Successfully creates a schedule with hourly repeat frequency ending on a specific date/time', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['hour'],
        frequencyOptions: {
          hour: {
            end: 'onDate',
            endDate: '2020-03-26',
            endTime: '10:45 AM',
            interval: 1,
          },
        },
        name: 'Run every hour until date',
        startDate: '2020-03-25',
        startTime: '10:45 AM',
        timezone: 'America/New_York',
      });
    });

    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run every hour until date',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=HOURLY;UNTIL=20200326T144500Z',
    });
  });

  test('Successfully creates a schedule with daily repeat frequency', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['day'],
        frequencyOptions: {
          day: {
            end: 'never',
            interval: 1,
          },
        },
        name: 'Run daily',
        startDate: '2020-03-25',
        startTime: '10:45 AM',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run daily',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=DAILY',
    });
  });

  test('Successfully creates a schedule with weekly repeat frequency on mon/wed/fri', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['week'],
        frequencyOptions: {
          week: {
            end: 'never',
            daysOfWeek: [RRule.MO, RRule.WE, RRule.FR],
            interval: 1,
            occurrences: 1,
          },
        },
        name: 'Run weekly on mon/wed/fri',
        startDate: '2020-03-25',
        startTime: '10:45 AM',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run weekly on mon/wed/fri',
      extra_data: {},
      rrule: `DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=${RRule.MO},${RRule.WE},${RRule.FR}`,
    });
  });

  test('Successfully creates a schedule with monthly repeat frequency on the first day of the month', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['month'],
        frequencyOptions: {
          month: {
            end: 'never',
            interval: 1,
            occurrences: 1,
            runOn: 'day',
            runOnDayNumber: 1,
          },
        },
        name: 'Run on the first day of the month',
        startDate: '2020-04-01',
        startTime: '10:45 AM',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run on the first day of the month',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200401T104500 RRULE:INTERVAL=1;FREQ=MONTHLY;BYMONTHDAY=1',
    });
  });

  test('Successfully creates a schedule with monthly repeat frequency on the last tuesday of the month', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['month'],
        frequencyOptions: {
          month: {
            end: 'never',
            endDate: '2020-03-26',
            endTime: '11:00 AM',
            interval: 1,
            occurrences: 1,
            runOn: 'the',
            runOnTheDay: 'tuesday',
            runOnTheOccurrence: -1,
          },
        },
        name: 'Run monthly on the last Tuesday',
        startDate: '2020-03-31',
        startTime: '11:00 AM',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run monthly on the last Tuesday',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200331T110000 RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=-1;BYDAY=TU',
    });
  });

  test('Successfully creates a schedule with yearly repeat frequency on the first day of March', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['year'],
        frequencyOptions: {
          year: {
            end: 'never',
            interval: 1,
            occurrences: 1,
            runOn: 'day',
            runOnDayMonth: 3,
            runOnDayNumber: 1,
          },
        },
        name: 'Yearly on the first day of March',
        startTime: '12:00 AM',
        startDate: '2020-03-01',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the first day of March',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200301T000000 RRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=1',
    });
  });

  test('Successfully creates a schedule with yearly repeat frequency on the second Friday in April', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['year'],
        frequencyOptions: {
          year: {
            end: 'never',
            interval: 1,
            occurrences: 1,
            runOn: 'the',
            runOnTheOccurrence: 2,
            runOnTheDay: 'friday',
            runOnTheMonth: 4,
          },
        },
        name: 'Yearly on the second Friday in April',
        startTime: '11:15 AM',
        startDate: '2020-04-10',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the second Friday in April',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200410T111500 RRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=2;BYDAY=FR;BYMONTH=4',
    });
  });

  test('Successfully creates a schedule with yearly repeat frequency on the first weekday in October', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: ['year'],
        frequencyOptions: {
          year: {
            end: 'never',
            interval: 1,
            occurrences: 1,
            runOn: 'the',
            runOnTheOccurrence: 1,
            runOnTheDay: 'weekday',
            runOnTheMonth: 10,
          },
        },
        name: 'Yearly on the first weekday in October',
        startTime: '11:15 AM',
        startDate: '2020-04-10',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the first weekday in October',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200410T111500 RRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=1;BYDAY=MO,TU,WE,TH,FR;BYMONTH=10',
    });
  });

  test('should open with correct values and navigate through the Promptable fields properly', async () => {
    InventoriesAPI.read.mockResolvedValue({
      data: {
        count: 2,
        results: [
          {
            name: 'Foo',
            id: 1,
            url: '',
          },
          {
            name: 'Bar',
            id: 2,
            url: '',
          },
        ],
      },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: {
        related_search_fields: [],
        actions: {
          GET: {
            filterable: true,
          },
        },
      },
    });

    await act(async () =>
      wrapper.find('Button[aria-label="Prompt"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('WizardNavItem').length).toBe(3);
    expect(wrapper.find('WizardNavItem').at(0).prop('isCurrent')).toBe(true);

    await act(async () => {
      wrapper.find('td#check-action-item-1').find('input').simulate('click');
    });
    wrapper.update();

    expect(
      wrapper.find('td#check-action-item-1').find('input').prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('WizardFooterInternal').prop('onNext')()
    );
    wrapper.update();
    expect(wrapper.find('WizardNavItem').at(1).prop('isCurrent')).toBe(true);

    expect(wrapper.find('CredentialChip').length).toBe(2);

    wrapper.update();

    await act(async () => {
      wrapper.find('td#check-action-item-2').find('input').simulate('click');
    });
    wrapper.update();
    expect(
      wrapper.find('td#check-action-item-2').find('input').prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('WizardFooterInternal').prop('onNext')()
    );
    wrapper.update();
    await act(async () =>
      wrapper.find('WizardFooterInternal').prop('onNext')()
    );
    wrapper.update();
    expect(wrapper.find('Wizard').length).toBe(0);
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        name: mockSchedule.name,
        frequency: [],
        skip_tags: '',
        startDate: '2021-01-28',
        startTime: '2:15 PM',
        timezone: 'America/New_York',
        credentials: [
          { id: 3, name: 'Credential 3', kind: 'ssh', url: '' },
          { name: 'schedule credential 1', id: 1, kind: 'vault' },
          { name: 'schedule credential 2', id: 2, kind: 'aws' },
        ],
      });
    });
    wrapper.update();

    expect(SchedulesAPI.update).toBeCalledWith(27, {
      extra_data: {},
      name: 'mock schedule',
      rrule:
        'DTSTART;TZID=America/New_York:20210128T141500 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
      skip_tags: '',
    });
    expect(SchedulesAPI.disassociateCredential).toBeCalledWith(27, 75);

    expect(SchedulesAPI.associateCredential).toBeCalledWith(27, 3);
  });

  test('should submit updated static form values, but original prompt form values', async () => {
    InventoriesAPI.read.mockResolvedValue({
      data: {
        count: 2,
        results: [
          {
            name: 'Foo',
            id: 1,
            url: '',
          },
          {
            name: 'Bar',
            id: 2,
            url: '',
          },
        ],
      },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: {
        related_search_fields: [],
        actions: {
          GET: {
            filterable: true,
          },
        },
      },
    });
    await act(async () =>
      wrapper.find('input#schedule-name').simulate('change', {
        target: { value: 'foo', name: 'name' },
      })
    );
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[aria-label="Prompt"]').prop('onClick')()
    );
    wrapper.update();
    await act(async () => {
      wrapper.find('td#check-action-item-2').find('input').simulate('click');
    });
    wrapper.update();

    expect(
      wrapper.find('td#check-action-item-2').find('input').prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('WizardFooterInternal').prop('onClose')()
    );
    wrapper.update();
    expect(wrapper.find('Wizard').length).toBe(0);

    await act(async () =>
      wrapper.find('Button[aria-label="Save"]').prop('onClick')()
    );

    expect(SchedulesAPI.update).toBeCalledWith(27, {
      endDateTime: undefined,
      startDateTime: undefined,
      description: '',
      extra_data: {},
      name: 'foo',
      inventory: 702,
      rrule:
        'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
    });
  });

  test('should submit survey with default values properly, without opening prompt wizard', async () => {
    let scheduleSurveyWrapper;
    await act(async () => {
      scheduleSurveyWrapper = mountWithContexts(
        <ScheduleEdit
          schedule={mockSchedule}
          resource={{
            id: 700,
            type: 'job_template',
            iventory: 1,
            summary_fields: {
              credentials: [
                { name: 'job template credential', id: 75, kind: 'ssh' },
              ],
            },
            name: 'Foo Job Template',
            description: '',
          }}
          resourceDefaultCredentials={[]}
          launchConfig={{
            can_start_without_user_input: false,
            passwords_needed_to_start: [],
            ask_scm_branch_on_launch: false,
            ask_variables_on_launch: false,
            ask_tags_on_launch: false,
            ask_diff_mode_on_launch: false,
            ask_skip_tags_on_launch: false,
            ask_job_type_on_launch: false,
            ask_limit_on_launch: false,
            ask_verbosity_on_launch: false,
            ask_inventory_on_launch: true,
            ask_credential_on_launch: true,
            survey_enabled: true,
            variables_needed_to_start: [],
            credential_needed_to_start: true,
            inventory_needed_to_start: true,
            job_template_data: {
              name: 'Demo Job Template',
              id: 7,
              description: '',
            },
            defaults: {
              extra_vars: '---',
              diff_mode: false,
              limit: '',
              job_tags: '',
              skip_tags: '',
              job_type: 'run',
              verbosity: 0,
              inventory: {
                name: null,
                id: null,
              },
              scm_branch: '',
              credentials: [],
            },
          }}
          surveyConfig={{
            spec: [
              {
                question_name: 'text',
                question_description: '',
                required: true,
                type: 'text',
                variable: 'text',
                min: 0,
                max: 1024,
                default: 'text variable',
                choices: '',
                new_question: true,
              },
              {
                question_name: 'mc',
                question_description: '',
                required: true,
                type: 'multiplechoice',
                variable: 'mc',
                min: 0,
                max: 1024,
                default: 'first',
                choices: 'first\nsecond',
                new_question: true,
              },
            ],
          }}
        />
      );
    });
    scheduleSurveyWrapper.update();

    await act(async () => {
      scheduleSurveyWrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        frequency: [],
        frequencyOptions: {},
        name: 'Run once schedule',
        startDate: '2020-03-25',
        startTime: '10:00 AM',
        timezone: 'America/New_York',
      });
    });

    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run once schedule',
      extra_data: { mc: 'first', text: 'text variable' },
      rrule:
        'DTSTART;TZID=America/New_York:20200325T100000 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
    });
  });
});
