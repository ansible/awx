import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { HostsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryHostDetail from './InventoryHostDetail';
import mockHost from '../shared/data.host.json';

jest.mock('../../../api');

describe('User has edit permissions', () => {
  let wrapper;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostDetail host={mockHost} />);
    });
  });
  test('should render Details', async () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Name', 'localhost');
    assertDetail('Description', 'localhost description');
    assertDetail('Created', '10/28/2019, 9:26:54 PM');
    assertDetail('Last Modified', '10/29/2019, 8:18:41 PM');
    expect(wrapper.find(`Detail[label="Activity"] Sparkline`)).toHaveLength(1);
  });

  test('should show edit button for users with edit permission', () => {
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/inventories/inventory/3/hosts/2/edit');
  });

  test('expected api call is made for delete', async () => {
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(HostsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('Error dialog shown for failed deletion', async () => {
    HostsAPI.destroy.mockImplementationOnce(() => Promise.reject(new Error()));
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      (el) => el.length === 0
    );
  });
});

describe('User has read-only permissions', () => {
  let wrapper;
  beforeEach(async () => {
    const readOnlyHost = {
      ...mockHost,
      summary_fields: {
        ...mockHost.summary_fields,
        user_capabilities: {
          ...mockHost.summary_fields.user_capabilities,
        },
      },
    };
    readOnlyHost.summary_fields.user_capabilities.edit = false;
    readOnlyHost.summary_fields.recent_jobs = [];
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostDetail host={readOnlyHost} />);
    });
  });

  test('should hide activity stream when there are no recent jobs', async () => {
    expect(wrapper.find(`Detail[label="Activity"] Sparkline`)).toHaveLength(0);
    const activity_detail = wrapper.find(`Detail[label="Activity"]`).at(0);
    expect(activity_detail.prop('isEmpty')).toEqual(true);
  });

  test('should hide edit button for users without edit permission', async () => {
    expect(wrapper.find('Button[aria-label="edit"]').length).toBe(0);
  });
});

describe('Cannot delete a constructed inventory', () => {
  let wrapper;
  let history;
  jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useParams: () => ({
      id: 42,
      hostId: 3,
      inventoryType: 'constructed_inventory',
    }),
  }));

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: [`/inventories/constructed_inventory/1/hosts/1/details`],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/:inventoryType/:id/hosts/:id/details">
          <InventoryHostDetail host={mockHost} />
        </Route>,
        { context: { router: { history } } }
      );
    });
  });
  test('should not show edit button', () => {
    const editButton = wrapper.find('Button[aria-label="edit"]');
    expect(editButton.length).toBe(0);
    expect(wrapper.find('Button[aria-label="delete"]').length).toBe(0);
  });
});
