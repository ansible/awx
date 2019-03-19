import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import Search from '../../src/components/Search';

describe('<Search />', () => {
  let search;

  afterEach(() => {
    if (search) {
      search.unmount();
      search = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const columns = [{ name: 'Name', key: 'name', isSortable: true }];

    const searchBtn = 'button[aria-label="Search"]';
    const searchTextInput = 'input[aria-label="Search text input"]';

    const onSearch = jest.fn();

    search = mount(
      <I18nProvider>
        <Search
          sortedColumnKey="name"
          columns={columns}
          onSearch={onSearch}
        />
      </I18nProvider>
    );

    search.find(searchTextInput).instance().value = 'test-321';
    search.find(searchTextInput).simulate('change');
    search.find(searchBtn).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('test-321');
  });

  test('handleDropdownToggle properly updates state', async () => {
    const columns = [{ name: 'Name', key: 'name', isSortable: true }];
    const onSearch = jest.fn();
    const wrapper = mount(
      <I18nProvider>
        <Search
          sortedColumnKey="name"
          columns={columns}
          onSearch={onSearch}
        />
      </I18nProvider>
    ).find('Search');
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(false);
    wrapper.instance().handleDropdownToggle(true);
    expect(wrapper.state('isSearchDropdownOpen')).toEqual(true);
  });

  test('handleDropdownSelect properly updates state', async () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true },
      { name: 'Description', key: 'description', isSortable: true }
    ];
    const onSearch = jest.fn();
    const wrapper = mount(
      <I18nProvider>
        <Search
          sortedColumnKey="name"
          columns={columns}
          onSearch={onSearch}
        />
      </I18nProvider>
    ).find('Search');
    expect(wrapper.state('searchKey')).toEqual('name');
    wrapper.instance().handleDropdownSelect({ target: { innerText: 'Description' } });
    expect(wrapper.state('searchKey')).toEqual('description');
  });
});
