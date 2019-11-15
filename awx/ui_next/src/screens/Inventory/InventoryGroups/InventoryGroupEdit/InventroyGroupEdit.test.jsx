import React from 'react';
import { GroupsAPI } from '@api';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import InventoryGroupEdit from './InventoryGroupEdit';

jest.mock('@api');
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
      initialEntries: ['/inventories/1/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroupEdit
          setBreadcrumb={jest.fn()}
          inventory={{ inventory: { id: 1 } }}
        />,
        {
          context: {
            router: {
              history,
              route: {
                match: {
                  params: { groupId: 13 },
                },
              },
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
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);
    expect(history.location.pathname).toEqual('/inventories/1/groups');
  });
  test('handleSubmit should call api', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);
    wrapper.find('InventoryGroupForm').prop('handleSubmit')({
      name: 'Bar',
      description: 'Ansible',
      variables: 'ying: yang',
    });
    expect(GroupsAPI.update).toBeCalled();
  });
});
