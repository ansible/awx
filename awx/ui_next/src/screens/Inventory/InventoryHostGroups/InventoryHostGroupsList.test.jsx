import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { HostsAPI } from '@api';
import InventoryHostGroupsList from './InventoryHostGroupsList';

jest.mock('@api');

const mockGroups = [
  {
    id: 1,
    type: 'group',
    name: 'foo',
    inventory: 1,
    url: '/api/v2/groups/1',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 2,
    type: 'group',
    name: 'bar',
    inventory: 1,
    url: '/api/v2/groups/2',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 3,
    type: 'group',
    name: 'baz',
    inventory: 1,
    url: '/api/v2/groups/3',
    summary_fields: {
      inventory: {
        id: 1,
      },
      user_capabilities: {
        delete: false,
        edit: false,
      },
    },
  },
];

describe('<InventoryHostGroupsList />', () => {
  let wrapper;

  beforeEach(async () => {
    HostsAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    HostsAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/3/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/inventories/inventory/:id/hosts/:hostId/groups"
          component={() => <InventoryHostGroupsList />}
        />,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('InventoryHostGroupsList').length).toBe(1);
  });

  test('should fetch groups from api and render them in the list', async () => {
    expect(HostsAPI.readGroups).toHaveBeenCalled();
    expect(wrapper.find('InventoryHostGroupItem').length).toBe(3);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(false);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        true
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(true);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        false
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    HostsAPI.readGroups.mockImplementation(() => Promise.reject(new Error()));
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
