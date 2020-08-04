import React from 'react';
import { act } from 'react-dom/test-utils';
import { InstancesAPI } from '../../api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import InstanceToggle from './InstanceToggle';

jest.mock('../../api');

const mockInstance = {
  id: 1,
  type: 'instance',
  url: '/api/v2/instances/1/',
  related: {
    jobs: '/api/v2/instances/1/jobs/',
    instance_groups: '/api/v2/instances/1/instance_groups/',
  },
  uuid: '00000000-0000-0000-0000-000000000000',
  hostname: 'awx',
  created: '2020-07-14T19:03:49.000054Z',
  modified: '2020-08-05T19:17:18.080033Z',
  capacity_adjustment: '0.40',
  version: '13.0.0',
  capacity: 10,
  consumed_capacity: 0,
  percent_capacity_remaining: 100.0,
  jobs_running: 0,
  jobs_total: 67,
  cpu: 6,
  memory: 2087469056,
  cpu_capacity: 24,
  mem_capacity: 1,
  enabled: true,
  managed_by_policy: true,
};

describe('<InstanceToggle>', () => {
  const onToggle = jest.fn();
  const fetchInstances = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should show toggle off', async () => {
    const wrapper = mountWithContexts(
      <InstanceToggle
        instance={mockInstance}
        fetchInstances={fetchInstances}
        onToggle={onToggle}
      />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(InstancesAPI.update).toHaveBeenCalledWith(1, {
      enabled: false,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);
    expect(onToggle).toHaveBeenCalledWith(false);
    expect(fetchInstances).toHaveBeenCalledTimes(1);
  });

  test('should show toggle on', async () => {
    const wrapper = mountWithContexts(
      <InstanceToggle
        instance={{
          ...mockInstance,
          enabled: false,
        }}
        onToggle={onToggle}
        fetchInstances={fetchInstances}
      />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(InstancesAPI.update).toHaveBeenCalledWith(1, {
      enabled: true,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);
    expect(onToggle).toHaveBeenCalledWith(true);
    expect(fetchInstances).toHaveBeenCalledTimes(1);
  });

  test('should show error modal', async () => {
    InstancesAPI.update.mockImplementation(() => {
      throw new Error('nope');
    });
    const wrapper = mountWithContexts(
      <InstanceToggle instance={mockInstance} />
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
