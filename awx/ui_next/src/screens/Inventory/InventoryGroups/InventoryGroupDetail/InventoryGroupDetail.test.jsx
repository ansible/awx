import React from 'react';
import { GroupsAPI } from '@api';
import { MemoryRouter, Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import InventoryGroupDetail from './InventoryGroupDetail';

jest.mock('@api');
const inventoryGroup = {
  name: 'Foo',
  description: 'Bar',
  variables: 'bizz: buzz',
  id: 1,
  created: '10:00',
  modified: '12:00',
  summary_fields: {
    created_by: {
      username: 'James',
    },
    modified_by: {
      username: 'Bond',
    },
  },
};
describe('<InventoryGroupDetail />', () => {
  let wrapper;
  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <MemoryRouter
          initialEntries={['/inventories/inventory/1/groups/1/edit']}
        >
          <Route
            path="/inventories/inventory/:id/groups/:groupId"
            component={() => (
              <InventoryGroupDetail inventoryGroup={inventoryGroup} />
            )}
          />
        </MemoryRouter>
      );
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('InventoryGroupDetail renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('should call api to delete the group', () => {
    wrapper.find('button[aria-label="Delete"]').simulate('click');
    expect(GroupsAPI.destroy).toBeCalledWith(1);
  });
  test('should navigate user to edit form on edit button click', async () => {
    wrapper.find('button[aria-label="Edit"]').prop('onClick');
    expect(
      wrapper
        .find('Router')
        .at(1)
        .prop('history').location.pathname
    ).toEqual('/inventories/inventory/1/groups/1/edit');
  });
  test('details shoudld render with the proper values', () => {
    expect(wrapper.find('Detail[label="Name"]').prop('value')).toBe('Foo');
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toBe(
      'Bar'
    );
    expect(wrapper.find('Detail[label="Created"]').prop('value')).toBe(
      '10:00 by James'
    );
    expect(wrapper.find('Detail[label="Modified"]').prop('value')).toBe(
      '12:00 by Bond'
    );
    expect(wrapper.find('VariablesInput').prop('value')).toBe('bizz: buzz');
  });
});
