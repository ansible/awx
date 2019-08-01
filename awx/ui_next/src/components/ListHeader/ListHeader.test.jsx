import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import ListHeader from './ListHeader';

describe('ListHeader', () => {
  const qsConfig = {
    namespace: 'item',
    defaultParams: { page: 1, page_size: 5, order_by: 'name' },
    integerFields: [],
  };
  const renderToolbarFn = jest.fn();

  test('initially renders without crashing', () => {
    const wrapper = mountWithContexts(
      <ListHeader
        itemCount={50}
        qsConfig={qsConfig}
        columns={[
          { name: 'foo', key: 'foo', isSearchable: true, isSortable: true },
        ]}
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
        columns={[
          { name: 'name', key: 'name', isSearchable: true, isSortable: true },
        ]}
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
    // since order_by = name is the default, that should be strip out of the search
    expect(history.location.search).toEqual('');
  });
});
