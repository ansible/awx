import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstancesAPI } from '../../../api';
import useDebounce from '../../../util/useDebounce';

import InstanceListItem from './InstanceListItem';

jest.mock('../../../api');
jest.mock('../../../util/useDebounce');

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

  beforeEach(() => {
    useDebounce.mockImplementation(fn => fn);
  });

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
          fetchInstances={() => {}}
        />
      );
    });
    expect(wrapper.find('InstanceListItem').length).toBe(1);
  });

  test('should calculate number of forks when slide changes', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
          fetchInstances={() => {}}
        />
      );
    });
    expect(wrapper.find('InstanceListItem').length).toBe(1);
    expect(wrapper.find('InstanceListItem__SliderForks').text()).toContain(
      '10 forks'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(1);
    });

    wrapper.update();
    expect(wrapper.find('InstanceListItem__SliderForks').text()).toContain(
      '24 forks'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(0);
    });
    wrapper.update();
    expect(wrapper.find('InstanceListItem__SliderForks').text()).toContain(
      '1 fork'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(0.5);
    });
    wrapper.update();
    expect(wrapper.find('InstanceListItem__SliderForks').text()).toContain(
      '12 forks'
    );
  });

  test('should render the proper data instance', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
          fetchInstances={() => {}}
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
    expect(
      wrapper
        .find('PFDataListCell[aria-label="capacity adjustment"]')
        .containsMatchingElement(<div>CPU 24</div>)
    );
    expect(
      wrapper
        .find('PFDataListCell[aria-label="capacity adjustment"]')
        .containsMatchingElement(<div>RAM 24</div>)
    );
    expect(wrapper.find('InstanceListItem__SliderForks').text()).toContain(
      '10 forks'
    );
  });

  test('should be checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected
          onSelect={() => {}}
          fetchInstances={() => {}}
        />
      );
    });
    expect(wrapper.find('input#instances-1').prop('checked')).toBe(true);
  });

  test('should display instance toggle', () => {
    expect(wrapper.find('InstanceToggle').length).toBe(1);
  });

  test('should display error', async () => {
    jest.useFakeTimers();
    InstancesAPI.update.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'patch',
            url: '/api/v2/instances/1',
            data: { capacity_adjustment: 0.30001 },
          },
          data: {
            capacity_adjustment: [
              'Ensure that there are no more than 3 digits in total.',
            ],
          },
          status: 400,
          statusText: 'Bad Request',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceListItem
          instance={instance[0]}
          isSelected={false}
          onSelect={() => {}}
          fetchInstances={() => {}}
        />,
        { context: { network: { handleHttpError: () => {} } } }
      );
    });
    await act(async () => {
      wrapper.update();
    });
    expect(wrapper.find('ErrorDetail').length).toBe(0);
    await act(async () => {
      wrapper.find('Slider').prop('onChange')(0.30001);
    });
    await act(async () => {
      wrapper.update();
    });
    jest.advanceTimersByTime(210);
    await act(async () => {
      wrapper.update();
    });
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
