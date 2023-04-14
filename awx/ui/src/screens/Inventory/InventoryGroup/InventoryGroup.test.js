import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { GroupsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InventoryGroup from './InventoryGroup';

jest.mock('../../../api');
describe('<InventoryGroup />', () => {
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 1,
      inventoryType: 'inventory',
    }),
  }));

  let wrapper;
  let history;
  const inventory = { id: 1, name: 'Foo' };

  beforeEach(async () => {
    GroupsAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        name: 'Foo',
        description: 'Bar',
        variables: 'bizz: buzz',
        summary_fields: {
          inventory: { id: 1 },
          created_by: { id: 1, username: 'Athena' },
          modified_by: { id: 1, username: 'Apollo' },
        },
        created: '2020-04-25T01:23:45.678901Z',
        modified: '2020-04-25T01:23:45.678901Z',
      },
    });
    history = createMemoryHistory({
      initialEntries: [`/inventories/inventory/1/groups/1/details`],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups">
          <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />
        </Route>,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });

  test('expect all tabs to exist, including Back to Groups', async () => {
    const routedTabs = wrapper.find('RoutedTabs');
    expect(routedTabs).toHaveLength(1);

    const tabs = routedTabs.prop('tabsArray');
    expect(tabs[0].link).toEqual(`/inventories/inventory/1/groups`);
    expect(tabs[1].name).toEqual('Details');
    expect(tabs[2].name).toEqual('Related Groups');
    expect(tabs[3].name).toEqual('Hosts');
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    history = createMemoryHistory({
      initialEntries: [`/inventories/inventory/1/groups/1/foobar`],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });

  test('should show content error when api throws error on initial render', async () => {
    GroupsAPI.readDetail.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroup inventory={inventory} />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});

describe('constructed inventory', () => {
  let wrapper;
  let history;
  const inventory = { id: 1, name: 'Foo' };

  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 1,
      groupId: 2,
      inventoryType: 'constructed_inventory',
    }),
  }));

  beforeEach(async () => {
    GroupsAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        name: 'Foo',
        description: 'Bar',
        variables: 'bizz: buzz',
        summary_fields: {
          inventory: { id: 1 },
          created_by: { id: 1, username: 'Athena' },
          modified_by: { id: 1, username: 'Apollo' },
        },
        created: '2020-04-25T01:23:45.678901Z',
        modified: '2020-04-25T01:23:45.678901Z',
      },
    });
    history = createMemoryHistory({
      initialEntries: [`/inventories/constructed_inventory/1/groups/1/details`],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/groups">
          <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />
        </Route>,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('Constructed Inventory expect all tabs to exist, including Back to Groups', () => {
    const routedTabs = wrapper.find('RoutedTabs');
    expect(routedTabs).toHaveLength(1);

    const tabs = routedTabs.prop('tabsArray');
    expect(tabs[0].link).toEqual(`/inventories/constructed_inventory/1/groups`);
    expect(tabs[1].name).toEqual('Details');
    expect(tabs[2].name).toEqual('Related Groups');
    expect(tabs[3].name).toEqual('Hosts');
  });
});
