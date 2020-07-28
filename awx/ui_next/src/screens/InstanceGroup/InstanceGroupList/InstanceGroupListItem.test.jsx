import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InstanceGroupListItem from './InstanceGroupListItem';

describe('<InstanceGroupListItem/>', () => {
  let wrapper;
  const instanceGroups = [
    {
      id: 1,
      name: 'Foo',
      type: 'instance_group',
      url: '/api/v2/instance_groups/1',
      capacity: 10,
      policy_instance_minimum: 10,
      policy_instance_percentage: 50,
      percent_capacity_remaining: 60,
      is_containerized: false,
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
      url: '/api/v2/instance_groups/2',
      capacity: 0,
      policy_instance_minimum: 0,
      policy_instance_percentage: 0,
      percent_capacity_remaining: 0,
      is_containerized: true,
      summary_fields: {
        user_capabilities: {
          edit: false,
          delete: false,
        },
      },
    },
  ];

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[1]}
          detailUrl="instance_groups/1/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('InstanceGroupListItem').length).toBe(1);
  });

  test('should render the proper data instance group', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[0]}
          detailUrl="instance_groups/1/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(
      wrapper.find('PFDataListCell[aria-label="instance group name"]').text()
    ).toBe('Foo');
    expect(wrapper.find('Progress').prop('value')).toBe(40);
    expect(
      wrapper.find('PFDataListCell[aria-label="instance group type"]').text()
    ).toBe('TypeInstance group');
    expect(wrapper.find('PencilAltIcon').length).toBe(1);
    expect(wrapper.find('input#select-instance-groups-1').prop('checked')).toBe(
      false
    );
  });

  test('should render the proper data container group', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[1]}
          detailUrl="instance_groups/2/details"
          isSelected={false}
          onSelect={() => {}}
        />
      );
    });
    expect(
      wrapper.find('PFDataListCell[aria-label="instance group name"]').text()
    ).toBe('Bar');

    expect(
      wrapper.find('PFDataListCell[aria-label="instance group type"]').text()
    ).toBe('TypeContainer group');
    expect(wrapper.find('PencilAltIcon').length).toBe(0);
  });

  test('should be checked', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[0]}
          detailUrl="instance_groups/1/details"
          isSelected
          onSelect={() => {}}
        />
      );
    });
    expect(wrapper.find('input#select-instance-groups-1').prop('checked')).toBe(
      true
    );
  });

  test('edit button shown to users with edit capabilities', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[0]}
          detailUrl="instance_groups/1/details"
          isSelected
          onSelect={() => {}}
        />
      );
    });

    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupListItem
          instanceGroup={instanceGroups[1]}
          detailsUrl="instance_group/2/details"
          isSelected
          onSelect={() => {}}
        />
      );
    });

    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
