import React from 'react';
import { GroupsAPI } from '@api';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import InventoryGroupAdd from './InventoryGroupAdd';

jest.mock('@api');

describe('<InventoryGroupAdd />', () => {
  let wrapper;
  let history;
  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroupAdd
          setBreadcrumb={() => {}}
          inventory={{ inventory: { id: 1 } }}
        />,
        {
          context: {
            router: {
              history,
            },
          },
        }
      );
    });
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('InventoryGroupAdd renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('cancel should navigate user to Inventory Groups List', async () => {
    await act(async () => {
      waitForElement(wrapper, 'isLoading', el => el.length === 0);
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/groups'
    );
  });
  test('handleSubmit should call api', async () => {
    await act(async () => {
      waitForElement(wrapper, 'isLoading', el => el.length === 0);
    });
    await act(async () => {
      wrapper.find('InventoryGroupForm').prop('handleSubmit')({
        name: 'Bar',
        description: 'Ansible',
        variables: 'ying: yang',
      });
    });

    expect(GroupsAPI.create).toBeCalled();
  });
});
