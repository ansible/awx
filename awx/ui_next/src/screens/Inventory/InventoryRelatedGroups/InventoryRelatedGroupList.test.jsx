import React from 'react';
import { act } from 'react-dom/test-utils';

import { GroupsAPI, InventoriesAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InventoryRelatedGroupList from './InventoryRelatedGroupList';
import mockRelatedGroups from '../shared/data.relatedGroups.json';

jest.mock('../../../api/models/Groups');
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/CredentialTypes');

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    groupId: 2,
  }),
}));

describe('<InventoryRelatedGroupList />', () => {
  let wrapper;

  beforeEach(async () => {
    GroupsAPI.readChildren.mockResolvedValue({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [
          'parents__search',
          'inventory__search',
          'inventory_sources__search',
          'created_by__search',
          'children__search',
          'modified_by__search',
          'hosts__search',
        ],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully ', () => {
    expect(wrapper.find('InventoryRelatedGroupList').length).toBe(1);
  });

  test('should fetch inventory group hosts from api and render them in the list', () => {
    expect(GroupsAPI.readChildren).toHaveBeenCalled();
    expect(InventoriesAPI.readGroupsOptions).toHaveBeenCalled();
    expect(wrapper.find('InventoryRelatedGroupListItem').length).toBe(3);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-group-2"]').props().checked
    ).toBe(false);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-2"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-2"]').props().checked
    ).toBe(true);
    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-2"]').invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-2"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
  });

  test('should show content error when api throws error on initial render', async () => {
    GroupsAPI.readChildren.mockResolvedValueOnce({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show add dropdown button according to permissions', async () => {
    GroupsAPI.readChildren.mockResolvedValueOnce({
      data: { ...mockRelatedGroups },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValueOnce({
      data: {
        actions: {
          GET: {},
        },
        related_search_fields: [
          'parents__search',
          'inventory__search',
          'inventory_sources__search',
          'created_by__search',
          'children__search',
          'modified_by__search',
          'hosts__search',
        ],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryRelatedGroupList />);
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('AddDropdown').length).toBe(0);
  });
});
