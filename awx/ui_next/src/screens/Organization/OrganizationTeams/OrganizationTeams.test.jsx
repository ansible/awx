import React from 'react';
import { shallow } from 'enzyme';

import { OrganizationsAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import OrganizationTeams from './OrganizationTeams';

jest.mock('@api');

const listData = {
  data: {
    count: 7,
    results: [
      { id: 1, name: 'one', url: '/org/team/1' },
      { id: 2, name: 'two', url: '/org/team/2' },
      { id: 3, name: 'three', url: '/org/team/3' },
      { id: 4, name: 'four', url: '/org/team/4' },
      { id: 5, name: 'five', url: '/org/team/5' },
    ],
  },
};

describe('<OrganizationTeams />', () => {
  beforeEach(() => {
    OrganizationsAPI.readTeams.mockResolvedValue(listData);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders succesfully', () => {
    shallow(
      <OrganizationTeams
        id={1}
        searchString=""
        location={{ search: '', pathname: '/organizations/1/teams' }}
      />
    );
  });

  test('should load teams on mount', () => {
    mountWithContexts(<OrganizationTeams id={1} searchString="" />).find(
      'OrganizationTeams'
    );
    expect(OrganizationsAPI.readTeams).toHaveBeenCalledWith(1, {
      page: 1,
      page_size: 5,
      order_by: 'name',
    });
  });

  test('should pass fetched teams to PaginatedDatalist', async () => {
    const wrapper = mountWithContexts(
      <OrganizationTeams id={1} searchString="" />
    );

    await sleep(0);
    wrapper.update();

    const list = wrapper.find('PaginatedDataList');
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
});
