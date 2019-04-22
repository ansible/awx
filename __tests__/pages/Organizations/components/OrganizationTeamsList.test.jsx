import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../enzymeHelpers';
import { sleep } from '../../../testUtils';
import OrganizationTeamsList from '../../../../src/pages/Organizations/components/OrganizationTeamsList';

const mockData = [
  { id: 1, name: 'one', url: '/org/team/1' },
  { id: 2, name: 'two', url: '/org/team/2' },
  { id: 3, name: 'three', url: '/org/team/3' },
  { id: 4, name: 'four', url: '/org/team/4' },
  { id: 5, name: 'five', url: '/org/team/5' },
];

describe('<OrganizationTeamsList />', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationTeamsList
        teams={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
      />
    );
  });

  // should navigate when datalisttoolbar changes sorting
  test('should navigate when DataListToolbar calls onSort prop', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <OrganizationTeamsList
        teams={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
      />, { context: { router: { history } } }
    );

    const toolbar = wrapper.find('DataListToolbar');
    expect(toolbar.prop('sortedColumnKey')).toEqual('name');
    expect(toolbar.prop('sortOrder')).toEqual('ascending');
    toolbar.prop('onSort')('name', 'descending');
    expect(history.location.search).toEqual('?order_by=-name');
    await sleep(0);
    wrapper.update();

    expect(toolbar.prop('sortedColumnKey')).toEqual('name');
    // TODO: this assertion required updating queryParams prop. Consider
    // fixing after #147 is done:
    // expect(toolbar.prop('sortOrder')).toEqual('descending');
    toolbar.prop('onSort')('name', 'ascending');
    expect(history.location.search).toEqual('?order_by=name');
  });

  test('should navigate to page when Pagination calls onSetPage prop', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <OrganizationTeamsList
        teams={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
      />, { context: { router: { history } } }
    );

    const pagination = wrapper.find('Pagination');
    pagination.prop('onSetPage')(2, 5);
    expect(history.location.search).toEqual('?page=2&page_size=5');
    wrapper.update();
    pagination.prop('onSetPage')(1, 25);
    expect(history.location.search).toEqual('?page=1&page_size=25');
  });
});
