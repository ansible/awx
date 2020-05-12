import React from 'react';
import { act } from 'react-dom/test-utils';
import { SchedulesAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ScheduleToggle from './ScheduleToggle';

jest.mock('../../../api');

const mockSchedule = {
  url: '/api/v2/schedules/1',
  rrule:
    'DTSTART;TZID=America/New_York:20200220T000000 RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1',
  id: 1,
  summary_fields: {
    unified_job_template: {
      id: 6,
      name: 'Mock JT',
      description: '',
      unified_job_type: 'job',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
  name: 'Mock JT Schedule',
  next_run: '2020-02-20T05:00:00Z',
  enabled: true,
};

describe('<ScheduleToggle>', () => {
  test('should should toggle off', async () => {
    const onToggle = jest.fn();
    const wrapper = mountWithContexts(
      <ScheduleToggle schedule={mockSchedule} onToggle={onToggle} />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(1, {
      enabled: false,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  test('should should toggle on', async () => {
    const onToggle = jest.fn();
    const wrapper = mountWithContexts(
      <ScheduleToggle
        schedule={{
          ...mockSchedule,
          enabled: false,
        }}
        onToggle={onToggle}
      />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(SchedulesAPI.update).toHaveBeenCalledWith(1, {
      enabled: true,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);
    expect(onToggle).toHaveBeenCalledWith(true);
  });

  test('should show error modal', async () => {
    SchedulesAPI.update.mockImplementation(() => {
      throw new Error('nope');
    });
    const wrapper = mountWithContexts(
      <ScheduleToggle schedule={mockSchedule} />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    wrapper.update();
    const modal = wrapper.find('AlertModal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('isOpen')).toEqual(true);

    act(() => {
      modal.invoke('onClose')();
    });
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(0);
  });
});
