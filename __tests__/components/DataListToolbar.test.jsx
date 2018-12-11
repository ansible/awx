import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import DataListToolbar from '../../src/components/DataListToolbar';

describe('<DataListToolbar />', () => {
  let toolbar;

  afterEach(() => {
    if (toolbar) {
      toolbar.unmount();
      toolbar = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const columns = [{ name: 'Name', key: 'name', isSortable: true }];

    const search = 'button[aria-label="Search"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const selectAll = 'input[aria-label="Select all"]';
    const sort = 'button[aria-label="Sort"]';

    const onSearch = jest.fn();
    const onSort = jest.fn();
    const onSelectAll = jest.fn();

    toolbar = mount(
      <I18nProvider>
        <DataListToolbar
          isAllSelected={false}
          sortedColumnKey="name"
          sortOrder="ascending"
          columns={columns}
          onSearch={onSearch}
          onSort={onSort}
          onSelectAll={onSelectAll}
        />
      </I18nProvider>
    );

    toolbar.find(sort).simulate('click');
    toolbar.find(selectAll).simulate('change', { target: { checked: false } });

    expect(onSelectAll).toHaveBeenCalledTimes(1);
    expect(onSort).toHaveBeenCalledTimes(1);
    expect(onSort).toBeCalledWith('name', 'descending');

    expect(onSelectAll).toHaveBeenCalledTimes(1);
    expect(onSelectAll.mock.calls[0][0]).toBe(false);

    toolbar.find(searchTextInput).instance().value = 'test-321';
    toolbar.find(searchTextInput).simulate('change');
    toolbar.find(search).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('test-321');
  });

  test('dropdown items sortable columns work', () => {
    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true },
      { name: 'Bar', key: 'bar', isSortable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' }
    ];

    const onSearch = jest.fn();
    const onSort = jest.fn();
    const onSelectAll = jest.fn();
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="foo"
        sortOrder="ascending"
        columns={multipleColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    const sortdropdownToggle = toolbar.find('.pf-l-toolbar__group.sortDropdownGroup .pf-l-toolbar__item button');
    expect(sortdropdownToggle.length).toBe(2);
    sortdropdownToggle.at(1).simulate('click');
    sortdropdownToggle.at(0).simulate('click');
    toolbar.update();
    const sortDropdownItems = toolbar.find('.pf-l-toolbar__group.sortDropdownGroup button.pf-c-dropdown__menu-item');
    expect(sortDropdownItems.length).toBe(2);
    const mockedSortEvent = { target: { innerText: 'Bar' } };
    sortDropdownItems.at(0).simulate('click', mockedSortEvent);
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="foo"
        sortOrder="descending"
        columns={multipleColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    toolbar.update();
    const sortdropdownToggleDescending = toolbar.find('.pf-l-toolbar__group.sortDropdownGroup .pf-l-toolbar__item button');
    expect(sortdropdownToggleDescending.length).toBe(2);
    sortdropdownToggleDescending.at(1).simulate('click');
    sortdropdownToggleDescending.at(0).simulate('click');
    toolbar.update();
    const sortDropdownItemsDescending = toolbar.find('.pf-l-toolbar__group.sortDropdownGroup button.pf-c-dropdown__menu-item');
    expect(sortDropdownItemsDescending.length).toBe(2);
    const mockedSortEventDescending = { target: { innerText: 'Bar' } };
    sortDropdownItems.at(0).simulate('click', mockedSortEventDescending);
    toolbar.update();
    const searchDropdownToggle = toolbar.find('.pf-c-dropdown.searchKeyDropdown button.pf-c-dropdown__toggle');
    expect(searchDropdownToggle.length).toBe(1);
    searchDropdownToggle.at(0).simulate('click');
    toolbar.update();
    const searchDropdownItems = toolbar.find('.pf-c-dropdown.searchKeyDropdown button.pf-c-dropdown__menu-item');
    expect(searchDropdownItems.length).toBe(3);
    const mockedSearchEvent = { target: { innerText: 'Bar' } };
    searchDropdownItems.at(0).simulate('click', mockedSearchEvent);
  });

  test('it displays correct sort icon', () => {
    const numericColumns = [{ name: 'ID', key: 'id', isSortable: true, isNumeric: true }];
    const alphaColumns = [{ name: 'Name', key: 'name', isSortable: true, isNumeric: false }];
    const onSearch = jest.fn();
    const onSort = jest.fn();
    const onSelectAll = jest.fn();
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="id"
        sortOrder="descending"
        columns={numericColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    const downNumericIcon = toolbar.find('SortNumericDownIcon');
    expect(downNumericIcon.length).toBe(1);
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="id"
        sortOrder="ascending"
        columns={numericColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    const upNumericIcon = toolbar.find('SortNumericUpIcon');
    expect(upNumericIcon.length).toBe(1);
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="name"
        sortOrder="descending"
        columns={alphaColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    const downAlphaIcon = toolbar.find('SortAlphaDownIcon');
    expect(downAlphaIcon.length).toBe(1);
    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={alphaColumns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
      />
    );
    const upAlphaIcon = toolbar.find('SortAlphaUpIcon');
    expect(upAlphaIcon.length).toBe(1);
  });
});
