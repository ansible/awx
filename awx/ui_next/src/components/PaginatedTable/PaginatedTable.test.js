import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PaginatedTable from './PaginatedTable';

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

describe('<PaginatedTable />', () => {
  test('should render item rows', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <PaginatedTable
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
        renderRow={item => (
          <tr key={item.id}>
            <td>{item.name}</td>
          </tr>
        )}
      />,
      { context: { router: { history } } }
    );

    const rows = wrapper.find('tr');
    expect(rows).toHaveLength(5);
    expect(rows.at(0).text()).toEqual('one');
    expect(rows.at(1).text()).toEqual('two');
    expect(rows.at(2).text()).toEqual('three');
    expect(rows.at(3).text()).toEqual('four');
    expect(rows.at(4).text()).toEqual('five');
  });

  test('should navigate page when changes', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <PaginatedTable
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
        renderRow={() => null}
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

  test('should navigate to page when page size changes', () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <PaginatedTable
        items={mockData}
        itemCount={7}
        queryParams={{
          page: 1,
          page_size: 5,
          order_by: 'name',
        }}
        qsConfig={qsConfig}
        renderRow={() => null}
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
