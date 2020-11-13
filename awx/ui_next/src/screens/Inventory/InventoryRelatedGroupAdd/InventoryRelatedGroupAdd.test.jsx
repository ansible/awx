import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { GroupsAPI } from '../../../api';
import InventoryRelatedGroupAdd from './InventoryRelatedGroupAdd';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    groupId: 2,
  }),
  useHistory: () => ({ push: jest.fn() }),
}));

describe('<InventoryRelatedGroupAdd/>', () => {
  let wrapper;
  const history = createMemoryHistory({
    initialEntries: ['/inventories/inventory/1/groups/2/nested_groups'],
  });

  beforeEach(() => {
    wrapper = mountWithContexts(<InventoryRelatedGroupAdd />);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should render properly', () => {
    expect(wrapper.find('InventoryRelatedGroupAdd').length).toBe(1);
  });

  test('should call api with proper data', async () => {
    GroupsAPI.create.mockResolvedValue({ data: { id: 3 } });
    await act(() =>
      wrapper.find('InventoryGroupForm').prop('handleSubmit')({
        name: 'foo',
        description: 'bar',
      })
    );
    expect(GroupsAPI.create).toBeCalledWith({
      inventory: 1,
      name: 'foo',
      description: 'bar',
    });
    expect(GroupsAPI.associateChildGroup).toBeCalledWith(2, 3);
  });

  test('cancel should navigate user to Inventory Groups List', async () => {
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/1/groups/2/nested_groups'
    );
  });

  test('should throw error on creation of group', async () => {
    GroupsAPI.create.mockRejectedValue({
      response: {
        config: {
          method: 'post',
          url: '/api/v2/groups/',
        },
        data: { detail: 'An error occurred' },
      },
    });
    await act(() =>
      wrapper.find('InventoryGroupForm').prop('handleSubmit')({
        name: 'foo',
        description: 'bar',
      })
    );
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });

  test('should throw error on association of group', async () => {
    GroupsAPI.create.mockResolvedValue({ data: { id: 3 } });
    GroupsAPI.associateChildGroup.mockRejectedValue({
      response: {
        config: {
          method: 'post',
          url: '/api/v2/groups/',
        },
        data: { detail: 'An error occurred' },
      },
    });
    await act(() =>
      wrapper.find('InventoryGroupForm').prop('handleSubmit')({
        name: 'foo',
        description: 'bar',
      })
    );
    expect(GroupsAPI.create).toBeCalledWith({
      inventory: 1,
      name: 'foo',
      description: 'bar',
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
