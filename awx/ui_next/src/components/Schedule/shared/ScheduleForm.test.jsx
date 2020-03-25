import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { SchedulesAPI } from '@api';
import ScheduleForm from './ScheduleForm';

jest.mock('@api/models/Schedules');

let wrapper;

const defaultFieldsVisible = () => {
  expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Start date/time"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Local time zone"]').length).toBe(1);
  expect(wrapper.find('FormGroup[label="Run frequency"]').length).toBe(1);
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
          <ScheduleForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
        );
      });
      wrapper.update();
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });
  describe('Cancel', () => {
    test('should make the appropriate callback', async () => {
      const handleCancel = jest.fn();
      SchedulesAPI.readZoneInfo.mockResolvedValue({
        data: [
          {
            name: 'America/New_York',
          },
        ],
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <ScheduleForm handleSubmit={jest.fn()} handleCancel={handleCancel} />
        );
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('button[aria-label="Cancel"]').simulate('click');
      });
      expect(handleCancel).toHaveBeenCalledTimes(1);
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
          <ScheduleForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
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
    });
    test('month run on options displayed correctly as date changes', async () => {
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-23T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(true);
      expect(wrapper.find('input#run-on-number + label').text()).toBe('Day 23');
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The fourth Monday'
      );
      expect(wrapper.find('input#run-on-last-day').length).toBe(0);
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-27T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(true);
      expect(wrapper.find('input#run-on-number + label').text()).toBe('Day 27');
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The fourth Friday'
      );
      expect(wrapper.find('input#run-on-last-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-last-day + label').text()).toBe(
        'The last Friday'
      );
    });
    test('month run on cleared when last day selected but date changes from one of the last seven days of the month', async () => {
      await act(async () => {
        wrapper.find('Radio#run-on-last-day').invoke('onChange')('lastDay', {
          target: { name: 'runOn' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-last-day').prop('checked')).toBe(true);
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-15T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-number + label').text()).toBe('Day 15');
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The third Sunday'
      );
      expect(wrapper.find('input#run-on-last-day').length).toBe(0);
      await act(async () => {
        wrapper.find('Radio#run-on-number').invoke('onChange')('number', {
          target: { name: 'runOn' },
        });
      });
      wrapper.update();
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
    });
    test('year run on options displayed correctly as date changes', async () => {
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-23T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(true);
      expect(wrapper.find('input#run-on-number + label').text()).toBe(
        'March 23'
      );
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The fourth Monday in March'
      );
      expect(wrapper.find('input#run-on-last-day').length).toBe(0);
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-27T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(true);
      expect(wrapper.find('input#run-on-number + label').text()).toBe(
        'March 27'
      );
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The fourth Friday in March'
      );
      expect(wrapper.find('input#run-on-last-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-last-day + label').text()).toBe(
        'The last Friday in March'
      );
    });
    test('occurrences field properly shown when that run on selection is made', async () => {
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
    test('year run on cleared when last day selected but date changes from one of the last seven days of the month', async () => {
      await act(async () => {
        wrapper.find('Radio#run-on-last-day').invoke('onChange')('lastDay', {
          target: { name: 'runOn' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-last-day').prop('checked')).toBe(true);
      await act(async () => {
        wrapper.find('input#schedule-start-datetime').simulate('change', {
          target: { value: '2020-03-15T01:45:00', name: 'startDateTime' },
        });
      });
      wrapper.update();
      expect(wrapper.find('input#run-on-number').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-number + label').text()).toBe(
        'March 15'
      );
      expect(wrapper.find('input#run-on-day').prop('checked')).toBe(false);
      expect(wrapper.find('input#run-on-day + label').text()).toBe(
        'The third Sunday in March'
      );
      expect(wrapper.find('input#run-on-last-day').length).toBe(0);
    });
    test('error shown when end date/time comes before start date/time', async () => {
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
        wrapper.find('input#schedule-end-datetime').invoke('onChange')(
          '2020-03-14T01:45:00',
          {
            target: { name: 'endDateTime' },
          }
        );
      });
      wrapper.update();

      setTimeout(() => {
        expect(wrapper.find('#schedule-end-datetime-helper').text()).toBe(
          'Please select an end date/time that comes after the start date/time.'
        );
      });
    });
  });
});
