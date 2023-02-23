import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { GroupsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryGroupDetail from './InventoryGroupDetail';

jest.mock('../../../api');

const inventoryGroup = {
  name: 'Foo',
  description: 'Bar',
  variables: 'bizz: buzz',
  id: 1,
  created: '2019-12-02T15:58:16.276813Z',
  modified: '2019-12-03T20:33:46.207654Z',
  summary_fields: {
    created_by: {
      username: 'James',
      id: 13,
    },
    modified_by: {
      username: 'Bond',
      id: 14,
    },
    user_capabilities: {
      delete: true,
      edit: true,
    },
  },
};

describe('<InventoryGroupDetail />', () => {
  let wrapper;
  let history;

  describe('User has full permissions', () => {
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useParams: () => ({
        id: 1,
        groupId: 3,
        inventoryType: 'inventory',
      }),
    }));
    beforeEach(async () => {
      await act(async () => {
        history = createMemoryHistory({
          initialEntries: ['/inventories/inventory/1/groups/1/details'],
        });
        wrapper = mountWithContexts(
          <Route path="/inventories/inventory/:id/groups/:groupId">
            <InventoryGroupDetail inventoryGroup={inventoryGroup} />
          </Route>,
          {
            context: {
              router: {
                history,
                route: {
                  location: history.location,
                  match: { params: { id: 1 } },
                },
              },
            },
          }
        );
        await waitForElement(
          wrapper,
          'ContentLoading',
          (el) => el.length === 0
        );
      });
    });
    afterEach(() => {
      jest.clearAllMocks();
    });
    test('InventoryGroupDetail renders successfully', () => {
      expect(wrapper.length).toBe(1);
    });

    test('should open delete modal and then call api to delete the group', async () => {
      expect(wrapper.find('Modal').length).toBe(1); // variables modal already mounted
      await act(async () => {
        wrapper.find('button[aria-label="Delete"]').simulate('click');
      });
      wrapper.update();
      expect(wrapper.find('Modal').length).toBe(2);
      await act(async () => {
        wrapper.find('Radio[id="radio-delete"]').invoke('onChange')();
      });
      wrapper.update();
      expect(
        wrapper.find('Button[aria-label="Confirm Delete"]').prop('isDisabled')
      ).toBe(false);
      await act(() =>
        wrapper.find('Button[aria-label="Confirm Delete"]').prop('onClick')()
      );
      expect(GroupsAPI.destroy).toBeCalledWith(1);
    });

    test('should navigate user to edit form on edit button click', async () => {
      wrapper.find('button[aria-label="Edit"]').simulate('click');
      expect(history.location.pathname).toEqual(
        '/inventories/inventory/1/groups/1/edit'
      );
    });

    test('details should render with the proper values and action buttons shown', () => {
      expect(wrapper.find('Detail[label="Name"]').prop('value')).toBe('Foo');
      expect(wrapper.find('Detail[label="Description"]').prop('value')).toBe(
        'Bar'
      );
      expect(wrapper.find('Detail[label="Created"]').length).toBe(1);
      expect(wrapper.find('Detail[label="Last Modified"]').length).toBe(1);
      expect(wrapper.find('VariablesDetail').prop('value')).toBe('bizz: buzz');

      expect(wrapper.find('button[aria-label="Edit"]').length).toBe(1);
      expect(wrapper.find('button[aria-label="Delete"]').length).toBe(1);
    });
  });

  describe('User has read-only permissions', () => {
    jest.mock('react-router-dom', () => ({
      ...jest.requireActual('react-router-dom'),
      useParams: () => ({
        id: 1,
        groupId: 3,
        inventoryType: 'inventory',
      }),
    }));
    test('should hide edit/delete buttons', async () => {
      const readOnlyGroup = {
        ...inventoryGroup,
        summary_fields: {
          ...inventoryGroup.summary_fields,
          user_capabilities: {
            delete: false,
            edit: false,
          },
        },
      };

      await act(async () => {
        history = createMemoryHistory({
          initialEntries: ['/inventories/inventory/1/groups/1/details'],
        });
        wrapper = mountWithContexts(
          <Route path="/inventories/inventory/:id/groups/:groupId">
            <InventoryGroupDetail inventoryGroup={readOnlyGroup} />
          </Route>,
          {
            context: {
              router: {
                history,
                route: {
                  location: history.location,
                  match: { params: { id: 1 } },
                },
              },
            },
          }
        );
        await waitForElement(
          wrapper,
          'ContentLoading',
          (el) => el.length === 0
        );
      });

      expect(wrapper.find('button[aria-label="Edit"]').length).toBe(0);
      expect(wrapper.find('button[aria-label="Delete"]').length).toBe(0);
    });
  });
  describe('Cannot edit or delete constructed inventory group', () => {
    beforeEach(async () => {
      await act(async () => {
        history = createMemoryHistory({
          initialEntries: ['/inventories/inventory/1/groups/1/details'],
        });
        wrapper = mountWithContexts(
          <Route path="/inventories/inventory/:id/groups/:groupId">
            <InventoryGroupDetail inventoryGroup={inventoryGroup} />
          </Route>,
          {
            context: {
              router: {
                history,
                route: {
                  location: history.location,
                  match: {
                    params: {
                      id: 1,
                      group: 2,
                      inventoryType: 'constructed_inventory',
                    },
                  },
                },
              },
            },
          }
        );
        await waitForElement(
          wrapper,
          'ContentLoading',
          (el) => el.length === 0
        );
      });
    });
    afterEach(() => {
      jest.clearAllMocks();
    });
    test('should not show edit button', () => {
      const editButton = wrapper.find('Button[aria-label="edit"]');
      expect(editButton.length).toBe(0);
      expect(wrapper.find('Button[aria-label="delete"]').length).toBe(0);
    });
  });
});
