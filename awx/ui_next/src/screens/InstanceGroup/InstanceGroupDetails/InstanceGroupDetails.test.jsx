import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import { InstanceGroupsAPI } from '../../../api';

import InstanceGroupDetails from './InstanceGroupDetails';

jest.mock('../../../api');

const instanceGroups = [
  {
    id: 1,
    name: 'Foo',
    type: 'instance_group',
    url: '/api/v2/instance_groups/1/',
    capacity: 10,
    policy_instance_minimum: 10,
    policy_instance_percentage: 50,
    percent_capacity_remaining: 60,
    is_containerized: false,
    is_isolated: false,
    created: '2020-07-21T18:41:02.818081Z',
    modified: '2020-07-24T20:32:03.121079Z',
    summary_fields: {
      user_capabilities: {
        edit: true,
        delete: true,
      },
    },
  },
  {
    id: 2,
    name: 'Bar',
    type: 'instance_group',
    url: '/api/v2/instance_groups/2/',
    capacity: 0,
    policy_instance_minimum: 0,
    policy_instance_percentage: 0,
    percent_capacity_remaining: 0,
    is_containerized: true,
    is_isolated: false,
    created: '2020-07-21T18:41:02.818081Z',
    modified: '2020-07-24T20:32:03.121079Z',
    summary_fields: {
      user_capabilities: {
        edit: false,
        delete: false,
      },
    },
  },
];

function expectDetailToMatch(wrapper, label, value) {
  const detail = wrapper.find(`Detail[label="${label}"]`);
  expect(detail).toHaveLength(1);
  expect(detail.prop('value')).toEqual(value);
}

describe('<InstanceGroupDetails/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails instanceGroup={instanceGroups[0]} />
      );
    });

    wrapper.update();

    expect(wrapper.find('Detail[label="Name"]').text()).toEqual(
      expect.stringContaining(instanceGroups[0].name)
    );
    expect(wrapper.find('Detail[label="Name"]')).toHaveLength(1);
    expectDetailToMatch(wrapper, 'Type', `Instance group`);
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(instanceGroups[0].created);
    expect(dates.at(1).prop('date')).toEqual(instanceGroups[0].modified);

    expect(
      wrapper.find('DetailBadge[label="Used capacity"]').prop('content')
    ).toBe(`${100 - instanceGroups[0].percent_capacity_remaining} %`);

    expect(
      wrapper
        .find('DetailBadge[label="Policy instance minimum"]')
        .prop('content')
    ).toBe(instanceGroups[0].policy_instance_minimum);

    expect(
      wrapper
        .find('DetailBadge[label="Policy instance percentage"]')
        .prop('content')
    ).toBe(`${instanceGroups[0].policy_instance_percentage} %`);
  });

  test('expected api call is made for delete', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/instance_groups/1/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails instanceGroup={instanceGroups[0]} />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(InstanceGroupsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(history.location.pathname).toBe('/instance_groups');
  });

  test('should not render delete button for tower instance group', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails instanceGroup={instanceGroups[1]} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });

  test('should not render delete button', async () => {
    instanceGroups[0].summary_fields.user_capabilities.delete = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails instanceGroup={instanceGroups[0]} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });

  test('should not render edit button', async () => {
    instanceGroups[0].summary_fields.user_capabilities.edit = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails instanceGroup={instanceGroups[0]} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(0);
  });

  test('should display isolated label', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupDetails
          instanceGroup={{ ...instanceGroups[0], is_isolated: true }}
        />
      );
    });
    wrapper.update();
    expect(
      wrapper.find('Label[aria-label="isolated instance"]').prop('children')
    ).toEqual('Isolated');
  });
});
