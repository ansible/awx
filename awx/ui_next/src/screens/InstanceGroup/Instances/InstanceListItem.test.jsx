import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InstanceListItem from './InstanceListItem';

const instance = [
  {
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
    modified: '2020-08-12T20:08:02.836748Z',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: true,
  },
];

describe('<InstanceListItem/>', () => {
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('InstanceListItem').length).toBe(1);
  });

  test('should render the proper data instance', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(
      wrapper.find('PFDataListCell[aria-label="instance host name"]').text()
    ).toBe('awx');
    expect(wrapper.find('Progress').prop('value')).toBe(40);
    expect(
      wrapper.find('PFDataListCell[aria-label="instance type"]').text()
    ).toBe('TypeAuto');
    expect(wrapper.find('input#instances-1').prop('checked')).toBe(false);
  });

  test('should be checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('input#instances-1').prop('checked')).toBe(true);
  });

  test('should display instance toggle', () => {
    expect(wrapper.find('InstanceToggle').length).toBe(1);
  });
});
