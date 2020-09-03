import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ListHeader from './ListHeader';

describe('ListHeader', () => {
  const qsConfig = {
    namespace: 'item',
    defaultParams: { page: 1, page_size: 5, order_by: 'foo' },
    integerFields: [],
  };
  const renderToolbarFn = jest.fn();

  test('initially renders without crashing', () => {
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={50}
        qsConfig={qsConfig}
        searchColumns={[
          { name: 'foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'foo', key: 'foo' }]}
        renderToolbar={renderToolbarFn}
      />
    );
    expect(wrapper.length).toBe(1);
    wrapper.unmount();
  });

  test('should navigate when DataListToolbar calls onSort prop', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={7}
        qsConfig={qsConfig}
        searchColumns={[
          { name: 'foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'foo', key: 'foo' }]}
      />,
      { context: { router: { history } } }
    );

    const toolbar = wrapper.find('DataListToolbar');
    toolbar.prop('onSort')('foo', 'descending');
    expect(history.location.search).toEqual('?item.order_by=-foo');
    toolbar.prop('onSort')('foo', 'ascending');
    // since order_by = name is the default, that should be strip out of the search
    expect(history.location.search).toEqual('');
  });

  test('should test clear all', () => {
    const query = '?item.page_size=5&item.name=foo';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={7}
        qsConfig={qsConfig}
        searchColumns={[
          { name: 'foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'foo', key: 'foo' }]}
      />,
      { context: { router: { history } } }
    );

    expect(history.location.search).toEqual(query);
    const toolbar = wrapper.find('DataListToolbar');
    toolbar.prop('clearAllFilters')();
    expect(history.location.search).toEqual('?item.page_size=5');
  });

  test('should test handle search', () => {
    const query = '?item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={7}
        qsConfig={qsConfig}
        searchColumns={[
          { name: 'foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'foo', key: 'foo' }]}
      />,
      { context: { router: { history } } }
    );

    expect(history.location.search).toEqual(query);
    const toolbar = wrapper.find('DataListToolbar');
    toolbar.prop('onSearch')('name__icontains', 'foo');
    expect(history.location.search).toEqual(
      '?item.name__icontains=foo&item.page_size=10'
    );
  });

  test('should test handle remove', () => {
    const query = '?item.name__icontains=foo&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={7}
        qsConfig={qsConfig}
        searchColumns={[
          { name: 'foo', key: 'foo__icontains', isDefault: true },
        ]}
        sortColumns={[{ name: 'foo', key: 'foo' }]}
      />,
      { context: { router: { history } } }
    );

    expect(history.location.search).toEqual(query);
    const toolbar = wrapper.find('DataListToolbar');
    toolbar.prop('onRemove')('name__icontains', 'foo');
    expect(history.location.search).toEqual('?item.page_size=10');
  });
});
