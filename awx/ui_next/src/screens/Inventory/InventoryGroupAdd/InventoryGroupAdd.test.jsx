import React from 'react';
import { Route } from 'react-router-dom';

import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { GroupsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InventoryGroupAdd from './InventoryGroupAdd';

jest.mock('../../../api');

describe('<InventoryGroupAdd />', () => {
  let wrapper;
  let history;
  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/add'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/inventory/:id/groups/add">
          <InventoryGroupAdd />
        </Route>,
        {
          context: {
            router: { history, route: { location: history.location } },
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
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/groups'
    );
  });
  test('handleSubmit should call api', async () => {
    GroupsAPI.create.mockResolvedValue({ data: {} });
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
