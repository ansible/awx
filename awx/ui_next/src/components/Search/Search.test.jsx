import React from 'react';
import {
  DataToolbar,
  DataToolbarContent,
} from '@patternfly/react-core/dist/umd/experimental';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
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
});
