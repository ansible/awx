import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import { InstanceGroupsAPI } from '../../../api';
import InstanceGroupList from './InstanceGroupList';

jest.mock('../../../api/models/InstanceGroups');

const instanceGroups = {
  data: {
    results: [
      {
        id: 1,
        name: 'Foo',
        type: 'instance_group',
        url: '/api/v2/instance_groups/1',
        consumed_capacity: 10,
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 2,
        name: 'tower',
        type: 'instance_group',
        url: '/api/v2/instance_groups/2',
        consumed_capacity: 42,
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 3,
        name: 'Bar',
        type: 'instance_group',
        url: '/api/v2/instance_groups/3',
        consumed_capacity: 42,
        summary_fields: { user_capabilities: { edit: true, delete: false } },
      },
    ],
    count: 3,
  },
};

const options = { data: { actions: { POST: true } } };

describe('<InstanceGroupList />', () => {
  let wrapper;

  test('should have data fetched and render 3 rows', async () => {
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);
    expect(wrapper.find('InstanceGroupListItem').length).toBe(3);
    expect(InstanceGroupsAPI.read).toBeCalled();
    expect(InstanceGroupsAPI.readOptions).toBeCalled();
  });

  test('should delete item successfully', async () => {
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);

    wrapper
      .find('input#select-instance-groups-1')
      .simulate('change', instanceGroups);
    wrapper.update();

    expect(wrapper.find('input#select-instance-groups-1').prop('checked')).toBe(
      true
    );

    await act(async () => {
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')();
    });
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );

    expect(InstanceGroupsAPI.destroy).toBeCalledWith(
      instanceGroups.data.results[0].id
    );
  });

  test('should not be able to delete tower instance group', async () => {
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);

    const instanceGroupIndex = [1, 2, 3];

    instanceGroupIndex.forEach(element => {
      wrapper
        .find(`input#select-instance-groups-${element}`)
        .simulate('change', instanceGroups);
      wrapper.update();

      expect(
        wrapper.find(`input#select-instance-groups-${element}`).prop('checked')
      ).toBe(true);
    });

    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
  });

  test('should thrown content error', async () => {
    InstanceGroupsAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'GET',
            url: '/api/v2/instance_groups',
          },
          data: 'An error occurred',
        },
      })
    );
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should render deletion error modal', async () => {
    InstanceGroupsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'DELETE',
            url: '/api/v2/instance_groups',
          },
          data: 'An error occurred',
        },
      })
    );
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);

    wrapper.find('input#select-instance-groups-1').simulate('change', 'a');
    wrapper.update();
    expect(wrapper.find('input#select-instance-groups-1').prop('checked')).toBe(
      true
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });

  test('should not render add button', async () => {
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    waitForElement(wrapper, 'InstanceGroupList', el => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});

describe('modifyInstanceGroups', () => {});
