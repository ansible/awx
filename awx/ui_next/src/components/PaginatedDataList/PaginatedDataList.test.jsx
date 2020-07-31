import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PaginatedDataList from './PaginatedDataList';

const mockData = [
  { id: 1, name: 'one', url: '/org/team/1' },
  { id: 2, name: 'two', url: '/org/team/2' },
  { id: 3, name: 'three', url: '/org/team/3' },
  { id: 4, name: 'four', url: '/org/team/4' },
  { id: 5, name: 'five', url: '/org/team/5' },
];

const qsConfig = {
  namespace: 'item',
  defaultParams: { page: 1, page_size: 5, order_by: 'name' },
  integerFields: ['page', 'page_size'],
};

describe('<PaginatedDataList />', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <PaginatedDataList
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
      />
    );
  });

  test('should navigate to page when Pagination calls onSetPage prop', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <PaginatedDataList
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
      />,
      { context: { router: { history } } }
    );

    const pagination = wrapper.find('Pagination').at(1);
    pagination.prop('onSetPage')(null, 2);
    expect(history.location.search).toEqual('?item.page=2');
    wrapper.update();
    pagination.prop('onSetPage')(null, 1);
    // since page = 1 is the default, that should be strip out of the search
    expect(history.location.search).toEqual('');
  });

  test('should navigate to page when Pagination calls onPerPageSelect prop', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <PaginatedDataList
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
      />,
      { context: { router: { history } } }
    );

    const pagination = wrapper.find('Pagination').at(1);
    pagination.prop('onPerPageSelect')(null, 25, 2);
    expect(history.location.search).toEqual('?item.page=2&item.page_size=25');
    wrapper.update();
    // since page_size = 5 is the default, that should be strip out of the search
    pagination.prop('onPerPageSelect')(null, 5, 2);
    expect(history.location.search).toEqual('?item.page=2');
  });
});
