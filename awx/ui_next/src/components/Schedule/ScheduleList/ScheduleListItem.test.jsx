import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ScheduleListItem from './ScheduleListItem';

const mockSchedule = {
  rrule:
    'DTSTART;TZID=America/New_York:20200220T000000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',
  id: 6,
  type: 'schedule',
  url: '/api/v2/schedules/6/',
  related: {},
  summary_fields: {
    unified_job_template: {
      id: 12,
      name: 'Mock JT',
      description: '',
      unified_job_type: 'job',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
  created: '2020-02-12T21:05:08.460029Z',
  modified: '2020-02-12T21:05:52.840596Z',
  name: 'Mock Schedule',
  description: 'every day for 1 time',
  extra_data: {},
  inventory: null,
  scm_branch: null,
  job_type: null,
  job_tags: null,
  skip_tags: null,
  limit: null,
  diff_mode: null,
  verbosity: null,
  unified_job_template: 12,
  enabled: true,
  dtstart: '2020-02-20T05:00:00Z',
  dtend: '2020-02-20T05:00:00Z',
  next_run: '2020-02-20T05:00:00Z',
  timezone: 'America/New_York',
  until: '',
};

const onSelect = jest.fn();

describe('ScheduleListItem', () => {
  let wrapper;
  describe('User has edit permissions', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <ScheduleListItem
          isSelected={false}
          onSelect={onSelect}
          schedule={mockSchedule}
        />
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('Name correctly shown with correct link', () => {
      expect(
        wrapper
          .find('DataListCell')
          .first()
          .text()
      ).toBe('Mock Schedule');
      expect(
        wrapper
          .find('DataListCell')
          .first()
          .find('Link')
          .props().to
      ).toBe('/templates/job_template/12/schedules/6/details');
    });
    test('Type correctly shown', () => {
      expect(
        wrapper
          .find('DataListCell')
          .at(1)
          .text()
      ).toBe('Playbook Run');
    });
    test('Edit button shown with correct link', () => {
      expect(wrapper.find('PencilAltIcon').length).toBe(1);
      expect(
        wrapper
          .find('Button')
          .find('Link')
          .props().to
      ).toBe('/templates/job_template/12/schedules/6/edit');
    });
    test('Toggle button enabled', () => {
      expect(
        wrapper
          .find('Switch')
          .first()
          .props().isDisabled
      ).toBe(false);
    });
    test('Clicking checkbox makes expected callback', () => {
      wrapper
        .find('DataListCheck')
        .first()
        .find('input')
        .simulate('change');
      expect(onSelect).toHaveBeenCalledTimes(1);
    });
  });
  describe('User has read-only permissions', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <ScheduleListItem
          isSelected={false}
          onSelect={onSelect}
          schedule={{
            ...mockSchedule,
            summary_fields: {
              ...mockSchedule.summary_fields,
              user_capabilities: {
                edit: false,
                delete: false,
              },
            },
          }}
        />
      );
    });
    afterAll(() => {
      wrapper.unmount();
    });
    test('Name correctly shown with correct link', () => {
      expect(
        wrapper
          .find('DataListCell')
          .first()
          .text()
      ).toBe('Mock Schedule');
      expect(
        wrapper
          .find('DataListCell')
          .first()
          .find('Link')
          .props().to
      ).toBe('/templates/job_template/12/schedules/6/details');
    });
    test('Type correctly shown', () => {
      expect(
        wrapper
          .find('DataListCell')
          .at(1)
          .text()
      ).toBe('Playbook Run');
    });
    test('Edit button hidden', () => {
      expect(wrapper.find('PencilAltIcon').length).toBe(0);
    });
    test('Toggle button disabled', () => {
      expect(
        wrapper
          .find('Switch')
          .first()
          .props().isDisabled
      ).toBe(true);
    });
  });
});
