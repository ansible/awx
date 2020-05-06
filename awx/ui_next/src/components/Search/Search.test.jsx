import React from 'react';
import {
  DataToolbar,
  DataToolbarContent,
} from '@patternfly/react-core/dist/umd/experimental';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { act } from 'react-dom/test-utils';
import Search from './Search';

describe('<Search />', () => {
  let search;

  const QS_CONFIG = {
    namespace: 'organization',
    dateFields: ['modified', 'created'],
    defaultParams: { page: 1, page_size: 5, order_by: 'name' },
    integerFields: ['page', 'page_size'],
  };

  afterEach(() => {
    if (search) {
      search = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const columns = [{ name: 'Name', key: 'name', isDefault: true }];

    const searchBtn = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';

    const onSearch = jest.fn();

    search = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} onSearch={onSearch} />
        </DataToolbarContent>
      </DataToolbar>
    );

    search.find(searchTextInput).instance().value = 'test-321';
    search.find(searchTextInput).simulate('change');
    search.find(searchBtn).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('handleDropdownToggle properly updates state', async () => {
    const columns = [{ name: 'Name', key: 'name', isDefault: true }];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} onSearch={onSearch} />
        </DataToolbarContent>
      </DataToolbar>
    ).find('Search');
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(false);
    wrapper.instance().handleDropdownToggle(true);
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(true);
  });

  test('handleDropdownSelect properly updates state', async () => {
    const columns = [
      { name: 'Name', key: 'name', isDefault: true },
      { name: 'Description', key: 'description' },
    ];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} onSearch={onSearch} />
        </DataToolbarContent>
      </DataToolbar>
    ).find('Search');
    expect(wrapper.state('searchKey')).toEqual('name');
    wrapper
      .instance()
      .handleDropdownSelect({ target: { innerText: 'Description' } });
    expect(wrapper.state('searchKey')).toEqual('description');
  });

  test('attempt to search with empty string', () => {
    const searchButton = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const columns = [{ name: 'Name', key: 'name', isDefault: true }];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} onSearch={onSearch} />
        </DataToolbarContent>
      </DataToolbar>
    );

    wrapper.find(searchTextInput).instance().value = '';
    wrapper.find(searchTextInput).simulate('change');
    wrapper.find(searchButton).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(0);
  });

  test('search with a valid string', () => {
    const searchButton = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const columns = [{ name: 'Name', key: 'name', isDefault: true }];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} onSearch={onSearch} />
        </DataToolbarContent>
      </DataToolbar>
    );

    wrapper.find(searchTextInput).instance().value = 'test-321';
    wrapper.find(searchTextInput).simulate('change');
    wrapper.find(searchButton).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('filter keys are properly labeled', () => {
    const columns = [
      { name: 'Name', key: 'name', isDefault: true },
      { name: 'Type', key: 'type', options: [['foo', 'Foo Bar!']] },
      { name: 'Description', key: 'description' },
    ];
    const query =
      '?organization.or__type=foo&organization.name=bar&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/${query}`],
    });
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search qsConfig={QS_CONFIG} columns={columns} />
        </DataToolbarContent>
      </DataToolbar>,
      { context: { router: { history } } }
    );
    const typeFilterWrapper = wrapper.find(
      'DataToolbarFilter[categoryName="Type"]'
    );
    expect(typeFilterWrapper.prop('chips')[0].key).toEqual('or__type:foo');
    const nameFilterWrapper = wrapper.find(
      'DataToolbarFilter[categoryName="Name"]'
    );
    expect(nameFilterWrapper.prop('chips')[0].key).toEqual('name:bar');
  });

  test('should test handle remove of option-based key', async () => {
    const qsConfigNew = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-type' },
      integerFields: [],
    };
    const columns = [
      {
        name: 'type',
        key: 'type',
        options: [['foo', 'Foo Bar!']],
        isDefault: true,
      },
    ];
    const query = '?item.or__type=foo&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const onRemove = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${qsConfigNew.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search
            qsConfig={qsConfigNew}
            columns={columns}
            onRemove={onRemove}
          />
        </DataToolbarContent>
      </DataToolbar>,
      { context: { router: { history } } }
    );
    expect(history.location.search).toEqual(query);
    // click remove button on chip
    await act(async () => {
      wrapper
        .find('.pf-c-chip button[aria-label="close"]')
        .at(0)
        .simulate('click');
    });
    expect(onRemove).toBeCalledWith('or__type', 'foo');
  });

  test('should test handle remove of option-based with empty string value', async () => {
    const qsConfigNew = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-type' },
      integerFields: [],
    };
    const columns = [
      {
        name: 'type',
        key: 'type',
        options: [['', 'manual']],
        isDefault: true,
      },
    ];
    const query = '?item.or__type=&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const onRemove = jest.fn();
    const wrapper = mountWithContexts(
      <DataToolbar
        id={`${qsConfigNew.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="md"
      >
        <DataToolbarContent>
          <Search
            qsConfig={qsConfigNew}
            columns={columns}
            onRemove={onRemove}
          />
        </DataToolbarContent>
      </DataToolbar>,
      { context: { router: { history } } }
    );
    expect(history.location.search).toEqual(query);
    // click remove button on chip
    await act(async () => {
      wrapper
        .find('.pf-c-chip button[aria-label="close"]')
        .at(0)
        .simulate('click');
    });
    expect(onRemove).toBeCalledWith('or__type', '');
  });
});
