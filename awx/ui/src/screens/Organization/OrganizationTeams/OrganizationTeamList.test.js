import React from 'react';
import { act } from 'react-dom/test-utils';

import { OrganizationsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import OrganizationTeamList from './OrganizationTeamList';

jest.mock('../../../api');

const listData = {
  data: {
    count: 7,
    results: [
      {
        id: 1,
        name: 'one',
        url: '/org/team/1',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 2,
        name: 'two',
        url: '/org/team/2',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 3,
        name: 'three',
        url: '/org/team/3',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 4,
        name: 'four',
        url: '/org/team/4',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
      {
        id: 5,
        name: 'five',
        url: '/org/team/5',
        summary_fields: { user_capabilities: { edit: true, delete: true } },
      },
    ],
  },
};

describe('<OrganizationTeamList />', () => {
  beforeEach(() => {
    OrganizationsAPI.readTeams.mockResolvedValue(listData);
    OrganizationsAPI.readTeamsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders successfully', async () => {
    await act(async () => {
      mountWithContexts(
        <OrganizationTeamList
          id={1}
          searchString=""
          location={{ search: '', pathname: '/organizations/1/teams' }}
        />
      );
    });
  });

  test('should load teams on mount', async () => {
    await act(async () => {
      mountWithContexts(<OrganizationTeamList id={1} searchString="" />).find(
        'OrganizationTeamList'
      );
    });
    expect(OrganizationsAPI.readTeams).toHaveBeenCalledWith(1, {
      page: 1,
      page_size: 5,
      order_by: 'name',
    });
  });

  test('should pass fetched teams to PaginatedTable', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationTeamList id={1} searchString="" />
      );
    });
    wrapper.update();

    const list = wrapper.find('PaginatedTable');
    expect(list.prop('items')).toEqual(listData.data.results);
    expect(list.prop('itemCount')).toEqual(listData.data.count);
    expect(list.prop('qsConfig')).toEqual({
      namespace: 'team',
      dateFields: ['modified', 'created'],
      defaultParams: {
        page: 1,
        page_size: 5,
        order_by: 'name',
      },
      integerFields: ['page', 'page_size'],
    });
  });

  test('should show content error for failed instance group fetch', async () => {
    OrganizationsAPI.readTeams.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationTeamList id={1} />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
