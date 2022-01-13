import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { LabelsAPI, InventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InventoryEdit from './InventoryEdit';

jest.mock('../../../api');

const mockInventory = {
  id: 1,
  type: 'inventory',
  url: '/api/v2/inventories/1/',
  summary_fields: {
    organization: {
      id: 1,
      name: 'Default',
      description: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
      copy: true,
      adhoc: true,
    },
    labels: {
      results: [
        { name: 'Sushi', id: 1 },
        { name: 'Major', id: 2 },
      ],
    },
  },
  created: '2019-10-04T16:56:48.025455Z',
  modified: '2019-10-04T16:56:48.025468Z',
  name: 'Inv no hosts',
  description: '',
  organization: 1,
  kind: '',
  host_filter: null,
  variables: '---',
  has_active_failures: false,
  total_hosts: 0,
  hosts_with_active_failures: 0,
  total_groups: 0,
  groups_with_active_failures: 0,
  has_inventory_sources: false,
  total_inventory_sources: 0,
  inventory_sources_with_failures: 0,
  pending_deletion: false,
};

const associatedInstanceGroups = [
  {
    id: 1,
    name: 'Foo',
  },
];

describe('<InventoryEdit />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    LabelsAPI.read.mockResolvedValue({
      data: {
        results: [
          { name: 'Sushi', id: 1 },
          { name: 'Major', id: 2 },
        ],
      },
    });

    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: {
        results: associatedInstanceGroups,
      },
    });
    history = createMemoryHistory({ initialEntries: ['/inventories'] });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryEdit inventory={mockInventory} />, {
        context: { router: { history } },
      });
    });
  });

  test('initially renders successfully', async () => {
    expect(wrapper.find('InventoryEdit').length).toBe(1);
  });

  test('called InventoriesAPI.readInstanceGroups', async () => {
    expect(InventoriesAPI.readInstanceGroups).toBeCalledWith(1);
  });

  test('handleCancel returns the user to inventory detail', async () => {
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/details'
    );
  });

  test('handleSubmit should post to the api', async () => {
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);
    const instanceGroups = [
      { name: 'Bizz', id: 2 },
      { name: 'Buzz', id: 3 },
    ];
    const labels = [{ name: 'label' }, { name: 'Major', id: 2 }];
    await act(async () => {
      wrapper.find('InventoryForm').prop('onSubmit')({
        name: 'Foo',
        id: 13,
        organization: { id: 1 },
        instanceGroups,
        labels,
      });
    });

    expect(InventoriesAPI.update).toHaveBeenCalledWith(1, {
      id: 13,
      labels: [{ name: 'label' }, { name: 'Major', id: 2 }],
      name: 'Foo',
      organization: 1,
    });

    expect(InventoriesAPI.associateLabel).toBeCalledWith(
      1,
      { name: 'label' },
      1
    );
    expect(InventoriesAPI.disassociateLabel).toBeCalledWith(1, {
      name: 'Sushi',
      id: 1,
    });
    expect(InventoriesAPI.orderInstanceGroups).toHaveBeenCalledWith(
      mockInventory.id,
      instanceGroups,
      associatedInstanceGroups
    );
  });
});
