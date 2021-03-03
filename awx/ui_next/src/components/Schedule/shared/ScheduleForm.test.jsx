import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { SchedulesAPI, JobTemplatesAPI, InventoriesAPI } from '../../../api';
import ScheduleForm from './ScheduleForm';

jest.mock('../../../api/models/Schedules');
jest.mock('../../../api/models/JobTemplates');
jest.mock('../../../api/models/Inventories');

const credentials = {
  data: {
    results: [
      { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
      { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
      { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
      { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
      { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
    ],
  },
};
const launchData = {
  data: {
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
    ask_credential_on_launch: false,
    survey_enabled: false,
    variables_needed_to_start: [],
    credential_needed_to_start: false,
    inventory_needed_to_start: true,
    job_template_data: {
      name: 'Demo Job Template',
      id: 7,
      description: '',
    },
  },
};
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
  },
  created: '2020-04-02T18:43:12.664142Z',
  modified: '2020-04-02T18:43:12.664185Z',
  name: 'mock schedule',
  description: 'test description',
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

let wrapper;

const defaultFieldsVisible = () => {
  expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Start date/time"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Local time zone"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Run frequency"]').length).toBe(1);
};

const nonRRuleValuesMatch = () => {
  expect(wrapper.find('input#schedule-name').prop('value')).toBe(
    'mock schedule'
  );
  expect(wrapper.find('input#schedule-description').prop('value')).toBe(
    'test description'
  );
  expect(wrapper.find('input#schedule-start-datetime').prop('value')).toBe(
    '2020-04-02T14:45:00'
  );
  expect(wrapper.find('select#schedule-timezone').prop('value')).toBe(
    'America/New_York'
  );
};

describe('<ScheduleForm />', () => {
  describe('Error', () => {
    test('should display error when error occurs while loading', async () => {
      SchedulesAPI.readZoneInfo.mockRejectedValue(
        new Error({
          response: {
            config: {
              method: 'get',
              url: '/api/v2/schedules/zoneinfo',
            },
            data: 'An error occurred',
            status: 500,
          },
        })
      );
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
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
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
      });
      wrapper.update();
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });
  describe('Cancel', () => {
    test('should make the appropriate callback', async () => {
      const handleCancel = jest.fn();
      JobTemplatesAPI.readLaunch.mockResolvedValue(launchData);

      SchedulesAPI.readCredentials.mockResolvedValue(credentials);
      SchedulesAPI.readZoneInfo.mockResolvedValue({
        data: [
          {
            name: 'America/New_York',
          },
        ],
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={handleCancel}
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
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
            resource={{ id: 23, type: 'job_template', inventory: 1 }}
          />
        );
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('button[aria-label="Cancel"]').simulate('click');
      });
      expect(handleCancel).toHaveBeenCalledTimes(1);
    });
  });
  describe('Prompted Schedule', () => {
    let promptWrapper;
    beforeEach(async () => {
      SchedulesAPI.readZoneInfo.mockResolvedValue({
        data: [
          {
            name: 'America/New_York',
          },
        ],
      });
      await act(async () => {
        promptWrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            resource={{
              id: 23,
              type: 'job_template',
              inventory: 1,
              summary_fields: {
                credentials: [],
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
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
            surveyConfig={{ spec: [{ required: true, default: '' }] }}
          />
        );
      });
      waitForElement(
        promptWrapper,
        'Button[aria-label="Prompt"]',
        el => el.length > 0
      );
    });
    afterEach(() => {
      promptWrapper.unmount();
      jest.clearAllMocks();
    });

    test('should open prompt modal with proper steps and default values', async () => {
      await act(async () =>
        promptWrapper.find('Button[aria-label="Prompt"]').prop('onClick')()
      );
      promptWrapper.update();
      waitForElement(promptWrapper, 'Wizard', el => el.length > 0);
      expect(promptWrapper.find('Wizard').length).toBe(1);
      expect(promptWrapper.find('StepName#inventory-step').length).toBe(2);
      expect(promptWrapper.find('StepName#preview-step').length).toBe(1);
      expect(promptWrapper.find('WizardNavItem').length).toBe(2);
    });

    test('should render disabled save button due to missing required surevy values', () => {
      expect(
        promptWrapper.find('Button[aria-label="Save"]').prop('isDisabled')
      ).toBe(true);
    });

    test('should update prompt modal data', async () => {
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
        promptWrapper.find('Button[aria-label="Prompt"]').prop('onClick')()
      );
      promptWrapper.update();
      expect(
        promptWrapper
          .find('WizardNavItem')
          .at(0)
          .prop('isCurrent')
      ).toBe(true);
      await act(async () => {
        promptWrapper
          .find('input[aria-labelledby="check-action-item-1"]')
          .simulate('change', {
            target: {
              checked: true,
            },
          });
      });
      promptWrapper.update();
      expect(
        promptWrapper
          .find('input[aria-labelledby="check-action-item-1"]')
          .prop('checked')
      ).toBe(true);
      await act(async () =>
        promptWrapper.find('WizardFooterInternal').prop('onNext')()
      );
      promptWrapper.update();
      expect(
        promptWrapper
          .find('WizardNavItem')
          .at(1)
          .prop('isCurrent')
      ).toBe(true);
      await act(async () =>
        promptWrapper.find('WizardFooterInternal').prop('onNext')()
      );
      promptWrapper.update();
      expect(promptWrapper.find('Wizard').length).toBe(0);
    });
    test('should render prompt button with disabled save button', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            resource={{
              id: 23,
              type: 'job_template',
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
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: true,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
          />
        );
      });
      waitForElement(
        wrapper,
        'Button[aria-label="Prompt"]',
        el => el.length > 0
      );
      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        true
      );
    });
  });
  describe('Add', () => {
    beforeAll(async () => {
      SchedulesAPI.readZoneInfo.mockResolvedValue({
        data: [
          {
            name: 'America/New_York',
          },
        ],
      });

      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            resource={{ id: 23, type: 'job_template', inventory: 1 }}
            launchConfig={{
              can_start_without_user_input: true,
              passwords_needed_to_start: [],
              ask_scm_branch_on_launch: false,
              ask_variables_on_launch: false,
              ask_tags_on_launch: false,
              ask_diff_mode_on_launch: false,
              ask_skip_tags_on_launch: false,
              ask_job_type_on_launch: false,
              ask_limit_on_launch: false,
              ask_verbosity_on_launch: false,
              ask_inventory_on_launch: false,
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: false,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
          />
        );
      });
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('initially renders expected fields and values', () => {
      expect(wrapper.find('ScheduleForm').length).toBe(1);
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-name').prop('value')).toBe('');
      expect(wrapper.find('input#schedule-description').prop('value')).toBe('');
      expect(
        wrapper.find('input#schedule-start-datetime').prop('value')
      ).toMatch(/\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d/);
      expect(wrapper.find('select#schedule-timezone').prop('value')).toBe(
        'America/New_York'
      );
      expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
        'none'
      );
    });
    test('correct frequency details fields and values shown when frequency changed to minute', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('minute', {
          target: { value: 'minute', key: 'minute', label: 'Minute' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
    });
    test('correct frequency details fields and values shown when frequency changed to hour', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('hour', {
          target: { value: 'hour', key: 'hour', label: 'Hour' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
    });
    test('correct frequency details fields and values shown when frequency changed to day', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('day', {
          target: { value: 'day', key: 'day', label: 'Day' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
    });
    test('correct frequency details fields and values shown when frequency changed to week', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('week', {
          target: { value: 'week', key: 'week', label: 'Week' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
    });
    test('correct frequency details fields and values shown when frequency changed to month', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('month', {
          target: { value: 'month', key: 'month', label: 'Month' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
      expect(wrapper.find('input#schedule-run-on-day').prop('checked')).toBe(
        true
      );
      expect(
        wrapper.find('input#schedule-run-on-day-number').prop('value')
      ).toBe(1);
      expect(wrapper.find('input#schedule-run-on-the').prop('checked')).toBe(
        false
      );
      expect(wrapper.find('select#schedule-run-on-day-month').length).toBe(0);
      expect(wrapper.find('select#schedule-run-on-the-month').length).toBe(0);
    });
    test('correct frequency details fields and values shown when frequency changed to year', async () => {
      const runFrequencySelect = wrapper.find(
        'FormGroup[label="Run frequency"] FormSelect'
      );
      await act(async () => {
        runFrequencySelect.invoke('onChange')('year', {
          target: { value: 'year', key: 'year', label: 'Year' },
        });
      });
      wrapper.update();
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
      expect(wrapper.find('input#schedule-run-on-day').prop('checked')).toBe(
        true
      );
      expect(
        wrapper.find('input#schedule-run-on-day-number').prop('value')
      ).toBe(1);
      expect(wrapper.find('input#schedule-run-on-the').prop('checked')).toBe(
        false
      );
      expect(wrapper.find('select#schedule-run-on-day-month').length).toBe(1);
      expect(wrapper.find('select#schedule-run-on-the-month').length).toBe(1);
    });
    test('occurrences field properly shown when end after selection is made', async () => {
      await act(async () => {
        wrapper
          .find('FormGroup[label="Run frequency"] FormSelect')
          .invoke('onChange')('minute', {
          target: { value: 'minute', key: 'minute', label: 'Minute' },
        });
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('Radio#end-after').invoke('onChange')('after', {
          target: { name: 'end' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#end-never').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(1);
      expect(wrapper.find('input#schedule-occurrences').prop('value')).toBe(1);
      await act(async () => {
        wrapper.find('Radio#end-never').invoke('onChange')('never', {
          target: { name: 'end' },
        });
      });
      wrapper.update();
    });
    test('error shown when end date/time comes before start date/time', async () => {
      await act(async () => {
        wrapper
          .find('FormGroup[label="Run frequency"] FormSelect')
          .invoke('onChange')('minute', {
          target: { value: 'minute', key: 'minute', label: 'Minute' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
      await act(async () => {
        wrapper.find('Radio#end-on-date').invoke('onChange')('onDate', {
          target: { name: 'end' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#end-never').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(true);
      expect(wrapper.find('#schedule-end-datetime-helper').length).toBe(0);
      await act(async () => {
        wrapper.find('input#schedule-end-datetime').simulate('change', {
          target: { name: 'endDateTime', value: '2020-03-14T01:45:00' },
        });
      });
      wrapper.update();

      await act(async () => {
        wrapper.find('input#schedule-end-datetime').simulate('blur');
      });
      wrapper.update();

      expect(wrapper.find('#schedule-end-datetime-helper').text()).toBe(
        'Please select an end date/time that comes after the start date/time.'
      );
    });
    test('error shown when on day number is not between 1 and 31', async () => {
      act(() => {
        wrapper.find('select[id="schedule-frequency"]').invoke('onChange')(
          {
            currentTarget: { value: 'month', type: 'change' },
            target: { name: 'frequency', value: 'month' },
          },
          'month'
        );
      });
      wrapper.update();

      act(() => {
        wrapper.find('input#schedule-run-on-day-number').simulate('change', {
          target: { value: 32, name: 'runOnDayNumber' },
        });
      });
      wrapper.update();

      expect(
        wrapper.find('input#schedule-run-on-day-number').prop('value')
      ).toBe(32);

      await act(async () => {
        wrapper.find('button[aria-label="Save"]').simulate('click');
      });
      wrapper.update();

      expect(wrapper.find('#schedule-run-on-helper').text()).toBe(
        'Please select a day number between 1 and 31.'
      );
    });
  });
  describe('Edit', () => {
    beforeEach(async () => {
      SchedulesAPI.readZoneInfo.mockResolvedValue({
        data: [
          {
            name: 'America/New_York',
          },
        ],
      });

      SchedulesAPI.readCredentials.mockResolvedValue(credentials);
    });
    afterEach(() => {
      wrapper.unmount();
      jest.clearAllMocks();
    });

    test('should  make API calls to fetch credentials, launch configuration, and survey configuration', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            schedule={{ inventory: null, ...mockSchedule }}
            resource={{ id: 23, type: 'job_template' }}
            launchConfig={{
              can_start_without_user_input: true,
              passwords_needed_to_start: [],
              ask_scm_branch_on_launch: false,
              ask_variables_on_launch: false,
              ask_tags_on_launch: false,
              ask_diff_mode_on_launch: false,
              ask_skip_tags_on_launch: false,
              ask_job_type_on_launch: false,
              ask_limit_on_launch: false,
              ask_verbosity_on_launch: false,
              ask_inventory_on_launch: false,
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: false,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
          />
        );
      });
      expect(SchedulesAPI.readCredentials).toBeCalledWith(27);
    });

    test('should not call API to get credentials ', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            resource={{ id: 23, type: 'job_template' }}
            launchConfig={{
              can_start_without_user_input: true,
              passwords_needed_to_start: [],
              ask_scm_branch_on_launch: false,
              ask_variables_on_launch: false,
              ask_tags_on_launch: false,
              ask_diff_mode_on_launch: false,
              ask_skip_tags_on_launch: false,
              ask_job_type_on_launch: false,
              ask_limit_on_launch: false,
              ask_verbosity_on_launch: false,
              ask_inventory_on_launch: false,
              ask_credential_on_launch: false,
              survey_enabled: false,
              variables_needed_to_start: [],
              credential_needed_to_start: false,
              inventory_needed_to_start: false,
              job_template_data: {
                name: 'Demo Job Template',
                id: 7,
                description: '',
              },
            }}
          />
        );
      });

      expect(SchedulesAPI.readCredentials).not.toBeCalled();
    });

    test('should render prompt button with enabled save button for project', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            resource={{
              id: 23,
              type: 'project',
              inventory: 2,
            }}
          />
        );
      });
      waitForElement(
        wrapper,
        'Button[aria-label="Prompt"]',
        el => el.length > 0
      );

      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        false
      );
    });

    test('initially renders expected fields and values with existing schedule that runs once', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            schedule={mockSchedule}
            launchConfig={{ inventory_needed_to_start: false }}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
      });
      expect(wrapper.find('ScheduleForm').length).toBe(1);
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      nonRRuleValuesMatch();
      expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
        'none'
      );
    });
    test('initially renders expected fields and values with existing schedule that runs every 10 minutes', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=10;FREQ=MINUTELY',
              dtend: null,
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
      });
      expect(wrapper.find('ScheduleForm').length).toBe(1);
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      nonRRuleValuesMatch();
      expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
        'minute'
      );
      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(10);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
    });
    test('initially renders expected fields and values with existing schedule that runs every hour 10 times', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=HOURLY;COUNT=10',
              dtend: '2020-04-03T03:45:00Z',
              until: '',
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
      });
      expect(wrapper.find('ScheduleForm').length).toBe(1);
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

      nonRRuleValuesMatch();
      expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
        'hour'
      );
      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(true);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
      expect(wrapper.find('input#schedule-occurrences').prop('value')).toBe(10);
    });
    test('initially renders expected fields and values with existing schedule that runs every day', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=DAILY',
              dtend: null,
              until: '',
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
        expect(wrapper.find('ScheduleForm').length).toBe(1);
        defaultFieldsVisible();
        expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);

        nonRRuleValuesMatch();
        expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
          'day'
        );
        expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
        expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
        expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
        expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      });
    });
    test('initially renders expected fields and values with existing schedule that runs every week on m/w/f until Jan 1, 2020', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=WEEKLY;BYDAY=MO,WE,FR;UNTIL=20210101T050000Z',
              dtend: '2020-10-30T18:45:00Z',
              until: '2021-01-01T00:00:00',
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
      });
      expect(wrapper.find('ScheduleForm').length).toBe(1);
      defaultFieldsVisible();
      expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="On days"]').length).toBe(1);
      expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);
      expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(0);

      nonRRuleValuesMatch();
      expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
        'week'
      );
      expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
      expect(wrapper.find('input#end-never').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
      expect(wrapper.find('input#end-on-date').prop('checked')).toBe(true);
      expect(
        wrapper.find('input#schedule-days-of-week-sun').prop('checked')
      ).toBe(false);
      expect(
        wrapper.find('input#schedule-days-of-week-mon').prop('checked')
      ).toBe(true);
      expect(
        wrapper.find('input#schedule-days-of-week-tue').prop('checked')
      ).toBe(false);
      expect(
        wrapper.find('input#schedule-days-of-week-wed').prop('checked')
      ).toBe(true);
      expect(
        wrapper.find('input#schedule-days-of-week-thu').prop('checked')
      ).toBe(false);
      expect(
        wrapper.find('input#schedule-days-of-week-fri').prop('checked')
      ).toBe(true);
      expect(
        wrapper.find('input#schedule-days-of-week-sat').prop('checked')
      ).toBe(false);
      expect(wrapper.find('input#schedule-end-datetime').prop('value')).toBe(
        '2021-01-01T00:00:00'
      );
    });
    test('initially renders expected fields and values with existing schedule that runs every month on the last weekday', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=MONTHLY;BYSETPOS=-1;BYDAY=MO,TU,WE,TH,FR',
              dtend: null,
              until: '',
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
        expect(wrapper.find('ScheduleForm').length).toBe(1);
        defaultFieldsVisible();
        expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);

        nonRRuleValuesMatch();
        expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
          'month'
        );
        expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
        expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
        expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
        expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
        expect(wrapper.find('input#schedule-run-on-day').prop('checked')).toBe(
          false
        );
        expect(wrapper.find('input#schedule-run-on-the').prop('checked')).toBe(
          true
        );
        expect(
          wrapper.find('select#schedule-run-on-the-occurrence').prop('value')
        ).toBe(-1);
        expect(
          wrapper.find('select#schedule-run-on-the-day').prop('value')
        ).toBe('weekday');
      });
    });
    test('initially renders expected fields and values with existing schedule that runs every year on the May 6', async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm
            handleSubmit={jest.fn()}
            handleCancel={jest.fn()}
            launchConfig={{ inventory_needed_to_start: false }}
            schedule={Object.assign(mockSchedule, {
              rrule:
                'DTSTART;TZID=America/New_York:20200402T144500 RRULE:INTERVAL=1;FREQ=YEARLY;BYMONTH=5;BYMONTHDAY=6',
              dtend: null,
              until: '',
            })}
            resource={{ id: 23, type: 'job_template' }}
          />
        );
        expect(wrapper.find('ScheduleForm').length).toBe(1);
        defaultFieldsVisible();
        expect(wrapper.find('FormGroup[label="End"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="Run every"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="Run on"]').length).toBe(1);
        expect(wrapper.find('FormGroup[label="End date/time"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="On days"]').length).toBe(0);
        expect(wrapper.find('FormGroup[label="Occurrences"]').length).toBe(0);

        nonRRuleValuesMatch();
        expect(wrapper.find('select#schedule-frequency').prop('value')).toBe(
          'year'
        );
        expect(wrapper.find('input#end-never').prop('checked')).toBe(true);
        expect(wrapper.find('input#end-after').prop('checked')).toBe(false);
        expect(wrapper.find('input#end-on-date').prop('checked')).toBe(false);
        expect(wrapper.find('input#schedule-run-every').prop('value')).toBe(1);
        expect(wrapper.find('input#schedule-run-on-day').prop('checked')).toBe(
          true
        );
        expect(wrapper.find('input#schedule-run-on-the').prop('checked')).toBe(
          false
        );
        expect(
          wrapper.find('select#schedule-run-on-day-month').prop('value')
        ).toBe(5);
        expect(
          wrapper.find('input#schedule-run-on-day-number').prop('value')
        ).toBe(6);
      });
    });
  });
});
