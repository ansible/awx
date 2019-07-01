import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { sleep } from '../../../testUtils/testUtils';
import PaginatedDataList from './PaginatedDataList';

const mockData = [
  { id: 1, name: 'one', url: '/org/team/1' },
  { id: 2, name: 'two', url: '/org/team/2' },
  { id: 3, name: 'three', url: '/org/team/3' },
  { id: 4, name: 'four', url: '/org/team/4' },
  { id: 5, name: 'five', url: '/org/team/5' },
  { id: 6, name: 'six', url: '/org/team/6' },
  { id: 7, name: 'seven', url: '/org/team/7' },
];

const qsConfig = {
  namespace: 'item',
  defaultParams: { page: 1, page_size: 5 },
  integerFields: [],
};

describe('<PaginatedDataList />', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initially renders succesfully', () => {
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

  test('should navigate when DataListToolbar calls onSort prop', async () => {
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

    const toolbar = wrapper.find('DataListToolbar');
    expect(toolbar.prop('sortedColumnKey')).toEqual('name');
    expect(toolbar.prop('sortOrder')).toEqual('ascending');
    toolbar.prop('onSort')('name', 'descending');
    expect(history.location.search).toEqual('?item.order_by=-name');
    await sleep(0);
    wrapper.update();

    expect(toolbar.prop('sortedColumnKey')).toEqual('name');
    // TODO: this assertion required updating queryParams prop. Consider
    // fixing after #147 is done:
    // expect(toolbar.prop('sortOrder')).toEqual('descending');
    toolbar.prop('onSort')('name', 'ascending');
    expect(history.location.search).toEqual('?item.order_by=name');
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

    const pagination = wrapper.find('Pagination');
    pagination.prop('onSetPage')(null, 2);
    expect(history.location.search).toEqual('?item.page=2');
    wrapper.update();
    pagination.prop('onSetPage')(null, 1);
    expect(history.location.search).toEqual('?item.page=1');
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

    const pagination = wrapper.find('Pagination');
    pagination.prop('onPerPageSelect')(null, 5);
    expect(history.location.search).toEqual('?item.page_size=5');
    wrapper.update();
    pagination.prop('onPerPageSelect')(null, 25);
    expect(history.location.search).toEqual('?item.page_size=25');
  });
  test('should navigate to correct current page when list items change', () => {
    const customQSConfig = {
      namespace: 'foo',
      defaultParams: { page: 7, page_size: 1 }, // show only 1 item per page
      integerFields: [],
    };
    const testParams = [5, 25, 0, -1]; // number of items
    const expected = [5, 5, 1, 1] // expected current page
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
        qsConfig={customQSConfig}
      />, { context: { router: { history } } }
    );
    testParams.forEach((param, i) => {
      wrapper.setProps({ itemCount: param });
      expect(history.location.search).toEqual(`?${customQSConfig.namespace}.page=${expected[i]}`)
      wrapper.update();
    })
    wrapper.unmount();
  });
});
