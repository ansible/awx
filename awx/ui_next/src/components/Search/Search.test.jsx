import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
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
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];

    const searchBtn = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';

    const onSearch = jest.fn();

    search = mountWithContexts(
      <Search
        qsConfig={QS_CONFIG}
        sortedColumnKey="name"
        columns={columns}
        onSearch={onSearch}
      />
    );

    search.find(searchTextInput).instance().value = 'test-321';
    search.find(searchTextInput).simulate('change');
    search.find(searchBtn).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('handleDropdownToggle properly updates state', async () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Search
        qsConfig={QS_CONFIG}
        sortedColumnKey="name"
        columns={columns}
        onSearch={onSearch}
      />
    ).find('Search');
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(false);
    wrapper.instance().handleDropdownToggle(true);
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(true);
  });

  test('handleDropdownSelect properly updates state', async () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
      {
        name: 'Description',
        key: 'description',
        isSortable: true,
        isSearchable: true,
      },
    ];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Search
        qsConfig={QS_CONFIG}
        sortedColumnKey="name"
        columns={columns}
        onSearch={onSearch}
      />
    ).find('Search');
    expect(wrapper.state('searchKey')).toEqual('name');
    wrapper
      .instance()
      .handleDropdownSelect({ target: { innerText: 'Description' } });
    expect(wrapper.state('searchKey')).toEqual('description');
  });
});
