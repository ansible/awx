import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  InstanceGroupsAPI,
  OrganizationsAPI,
  InventoriesAPI,
  UnifiedJobTemplatesAPI,
  SettingsAPI,
} from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InstanceGroupList from './InstanceGroupList';

jest.mock('../../../api/models/InstanceGroups');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/UnifiedJobTemplates');
jest.mock('../../../api/models/Settings');

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
        name: 'controlplan',
        type: 'instance_group',
        url: '/api/v2/instance_groups/2',
        consumed_capacity: 42,
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 3,
        name: 'default',
        type: 'instance_group',
        url: '/api/v2/instance_groups/2',
        consumed_capacity: 42,
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 4,
        name: 'Bar',
        type: 'instance_group',
        url: '/api/v2/instance_groups/3',
        consumed_capacity: 42,
        summary_fields: { user_capabilities: { edit: true, delete: false } },
      },
    ],
    count: 4,
  },
};

const options = { data: { actions: { POST: true } } };
const settings = {
  data: {
    DEFAULT_CONTROL_PLANE_QUEUE_NAME: 'controlplan',
    DEFAULT_EXECUTION_QUEUE_NAME: 'default',
  },
};

describe('<InstanceGroupList />', () => {
  let wrapper;

  beforeEach(() => {
    OrganizationsAPI.read.mockResolvedValue({ data: { count: 0 } });
    InventoriesAPI.read.mockResolvedValue({ data: { count: 0 } });
    UnifiedJobTemplatesAPI.read.mockResolvedValue({ data: { count: 0 } });
    InstanceGroupsAPI.read.mockResolvedValue(instanceGroups);
    InstanceGroupsAPI.readOptions.mockResolvedValue(options);
    SettingsAPI.readAll.mockResolvedValue(settings);
  });

  test('should have data fetched and render 3 rows', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);
    expect(wrapper.find('InstanceGroupListItem').length).toBe(4);
    expect(InstanceGroupsAPI.read).toBeCalled();
    expect(InstanceGroupsAPI.readOptions).toBeCalled();
  });

  test('should delete item successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', instanceGroups);
    wrapper.update();

    expect(
      wrapper.find('.pf-c-table__check').first().find('input').prop('checked')
    ).toBe(true);

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

  test('should not be able to delete controlplan or default instance group', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);

    const instanceGroupIndex = [0, 1, 2, 3];

    instanceGroupIndex.forEach((element) => {
      wrapper
        .find('.pf-c-table__check')
        .at(element)
        .find('input')
        .simulate('change', instanceGroups);
      wrapper.update();

      expect(
        wrapper
          .find('.pf-c-table__check')
          .at(element)
          .find('input')
          .prop('checked')
      ).toBe(true);
    });

    expect(wrapper.find('Button[aria-label="Delete"]').prop('isDisabled')).toBe(
      true
    );
  });

  test('should thrown content error', async () => {
    InstanceGroupsAPI.read = jest.fn();
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
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    await waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should render deletion error modal', async () => {
    InstanceGroupsAPI.destroy = jest.fn();
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
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupList />);
    });
    waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', 'a');
    wrapper.update();
    expect(
      wrapper.find('.pf-c-table__check').first().find('input').prop('checked')
    ).toBe(true);

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
    waitForElement(wrapper, 'InstanceGroupList', (el) => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});

describe('modifyInstanceGroups', () => {});
