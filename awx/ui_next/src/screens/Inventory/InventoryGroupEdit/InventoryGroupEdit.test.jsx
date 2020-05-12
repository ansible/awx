import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { GroupsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import InventoryGroupEdit from './InventoryGroupEdit';

jest.mock('../../../api');
GroupsAPI.readDetail.mockResolvedValue({
  data: {
    name: 'Foo',
    description: 'Bar',
    variables: 'bizz: buzz',
  },
});
describe('<InventoryGroupEdit />', () => {
  let wrapper;
  let history;
  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/2/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/inventory/:id/groups/:groupId/edit">
          <InventoryGroupEdit inventoryGroup={{ id: 2 }} />
        </Route>,
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
  test('InventoryGroupEdit renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('cancel should navigate user to Inventory Groups List', async () => {
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/groups/2'
    );
  });
  test('handleSubmit should call api', async () => {
    wrapper.find('InventoryGroupForm').prop('handleSubmit')({
      name: 'Bar',
      description: 'Ansible',
      variables: 'ying: yang',
    });
    expect(GroupsAPI.update).toBeCalled();
  });
});
