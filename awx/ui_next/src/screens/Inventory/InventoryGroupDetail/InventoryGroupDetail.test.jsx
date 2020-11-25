import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { GroupsAPI } from '../../../api';
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
  },
};

describe('<InventoryGroupDetail />', () => {
  let wrapper;
  let history;
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
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('InventoryGroupDetail renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should open delete modal and then call api to delete the group', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Delete"]').simulate('click');
    });
    await waitForElement(wrapper, 'Modal', el => el.length === 1);
    expect(wrapper.find('Modal').length).toBe(1);
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

  test('details should render with the proper values', () => {
    expect(wrapper.find('Detail[label="Name"]').prop('value')).toBe('Foo');
    expect(wrapper.find('Detail[label="Description"]').prop('value')).toBe(
      'Bar'
    );
    expect(wrapper.find('Detail[label="Created"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last Modified"]').length).toBe(1);
    expect(wrapper.find('VariablesDetail').prop('value')).toBe('bizz: buzz');
  });
});
