import React from 'react';
import { act } from 'react-dom/test-utils';
import { RRule } from 'rrule';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import {
  SchedulesAPI,
  InventoriesAPI,
  CredentialsAPI,
  CredentialTypesAPI,
} from '../../../api';
import ScheduleEdit from './ScheduleEdit';

jest.mock('../../../api/models/Schedules');
jest.mock('../../../api/models/JobTemplates');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Credentials');
jest.mock('../../../api/models/CredentialTypes');

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
      { name: 'schedule credential 1', id: 1, kind: 'vault' },
      { name: 'schedule credential 2', id: 2, kind: 'aws' },
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
      { id: 1, name: 'Credential 1', kind: 'ssh', url: '' },
      { id: 2, name: 'Credential 2', kind: 'ssh', url: '' },
      { id: 3, name: 'Credential 3', kind: 'ssh', url: '' },
    ],
  },
});

CredentialsAPI.readOptions.mockResolvedValue({
  data: { related_search_fields: [], actions: { GET: { filterabled: true } } },
});

SchedulesAPI.update.mockResolvedValue({
  data: {
    id: 27,
  },
});

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
    await act(async () => {
      wrapper = mountWithContexts(
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
          }}
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
            },
          }}
          surveyConfig={{}}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('Successfully creates a schedule with repeat frequency: None (run once)', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'none',
        interval: 1,
        name: 'Run once schedule',
        startDateTime: '2020-03-25T10:00:00',
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
        end: 'after',
        frequency: 'minute',
        interval: 10,
        name: 'Run every 10 minutes 10 times',
        occurrences: 10,
        startDateTime: '2020-03-25T10:30:00',
        timezone: 'America/New_York',
      });
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run every 10 minutes 10 times',
      extra_data: {},
      occurrences: 10,
      rrule:
        'DTSTART;TZID=America/New_York:20200325T103000 RRULE:INTERVAL=10;FREQ=MINUTELY;COUNT=10',
    });
  });
  test('Successfully creates a schedule with hourly repeat frequency ending on a specific date/time', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run every hour until date',
      extra_data: {},
      rrule:
        'DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=HOURLY;UNTIL=20200326T104500',
    });
  });
  test('Successfully creates a schedule with daily repeat frequency', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
        description: 'test description',
        end: 'never',
        frequency: 'day',
        interval: 1,
        name: 'Run daily',
        startDateTime: '2020-03-25T10:45:00',
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run weekly on mon/wed/fri',
      extra_data: {},
      occurrences: 1,
      rrule: `DTSTART;TZID=America/New_York:20200325T104500 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=${RRule.MO},${RRule.WE},${RRule.FR}`,
    });
  });
  test('Successfully creates a schedule with monthly repeat frequency on the first day of the month', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run on the first day of the month',
      extra_data: {},
      occurrences: 1,
      rrule:
        'DTSTART;TZID=America/New_York:20200401T104500 RRULE:INTERVAL=1;FREQ=MONTHLY;BYMONTHDAY=1',
    });
  });
  test('Successfully creates a schedule with monthly repeat frequency on the last tuesday of the month', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Run monthly on the last Tuesday',
      extra_data: {},
      occurrences: 1,
      runOnTheOccurrence: -1,
      rrule:
        'DTSTART;TZID=America/New_York:20200331T110000 RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=-1;BYDAY=TU',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the first day of March', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the first day of March',
      extra_data: {},
      occurrences: 1,
      rrule:
        'DTSTART;TZID=America/New_York:20200301T000000 RRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=3;BYMONTHDAY=1',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the second Friday in April', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the second Friday in April',
      extra_data: {},
      occurrences: 1,
      runOnTheOccurrence: 2,
      rrule:
        'DTSTART;TZID=America/New_York:20200410T111500 RRULE:INTERVAL=1;FREQ=YEARLY;BYSETPOS=2;BYDAY=FR;BYMONTH=4',
    });
  });
  test('Successfully creates a schedule with yearly repeat frequency on the first weekday in October', async () => {
    await act(async () => {
      wrapper.find('Formik').invoke('onSubmit')({
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
    expect(SchedulesAPI.update).toHaveBeenCalledWith(27, {
      description: 'test description',
      name: 'Yearly on the first weekday in October',
      extra_data: {},
      occurrences: 1,
      runOnTheOccurrence: 1,
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
    expect(
      wrapper
        .find('WizardNavItem')
        .at(0)
        .prop('isCurrent')
    ).toBe(true);

    await act(async () => {
      wrapper
        .find('input[aria-labelledby="check-action-item-1"]')
        .simulate('change', {
          target: {
            checked: true,
          },
        });
    });
    wrapper.update();

    expect(
      wrapper
        .find('input[aria-labelledby="check-action-item-1"]')
        .prop('checked')
    ).toBe(true);
    await act(async () =>
      wrapper.find('WizardFooterInternal').prop('onNext')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('WizardNavItem')
        .at(1)
        .prop('isCurrent')
    ).toBe(true);

    expect(wrapper.find('CredentialChip').length).toBe(3);

    wrapper.update();

    await act(async () => {
      wrapper
        .find('input[aria-labelledby="check-action-item-3"]')
        .simulate('change', {
          target: {
            checked: true,
          },
        });
    });
    wrapper.update();
    expect(
      wrapper
        .find('input[aria-labelledby="check-action-item-3"]')
        .prop('checked')
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
        end: 'never',
        endDateTime: '2021-01-29T14:15:00',
        frequency: 'none',
        occurrences: 1,
        runOn: 'day',
        runOnDayMonth: 1,
        runOnDayNumber: 1,
        runOnTheDay: 'sunday',
        runOnTheMonth: 1,
        runOnTheOccurrence: 1,
        skip_tags: '',
        startDateTime: '2021-01-28T14:15:00',
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
      occurrences: 1,
      runOnTheOccurrence: 1,
      rrule:
        'DTSTART;TZID=America/New_York:20210128T141500 RRULE:COUNT=1;FREQ=MINUTELY',
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
      wrapper
        .find('input[aria-labelledby="check-action-item-2"]')
        .simulate('change', {
          target: {
            checked: true,
          },
        });
    });
    wrapper.update();

    expect(
      wrapper
        .find('input[aria-labelledby="check-action-item-2"]')
        .prop('checked')
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
      description: '',
      extra_data: {},
      occurrences: 1,
      runOnTheOccurrence: 1,
      name: 'foo',
      inventory: 702,
      rrule:
        'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;COUNT=1;FREQ=MINUTELY',
    });
  });
});
