import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DataListToolbar from './DataListToolbar';

describe('<DataListToolbar />', () => {
  let toolbar;

  const QS_CONFIG = {
    namespace: 'organization',
    dateFields: ['modified', 'created'],
    defaultParams: { page: 1, page_size: 5, order_by: 'name' },
    integerFields: ['page', 'page_size'],
  };

  afterEach(() => {
    if (toolbar) {
      toolbar.unmount();
      toolbar = null;
    }
  });

  const onSearch = jest.fn();
  const onSort = jest.fn();
  const onSelectAll = jest.fn();

  test('it triggers the expected callbacks', () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];

    const search = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const selectAll = 'input[aria-label="Select all"]';
    const sort = 'button[aria-label="Sort"]';

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        isAllSelected={false}
        showExpandCollapse
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={columns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        showSelectAll
      />
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
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('dropdown items sortable/searchable columns work', () => {
    const sortDropdownToggleSelector = 'button[id="awx-sort"]';
    const searchDropdownToggleSelector = 'button[id="awx-search"]';
    const sortDropdownMenuItems =
      'DropdownMenu > ul[aria-labelledby="awx-sort"]';
    const searchDropdownMenuItems =
      'DropdownMenu > ul[aria-labelledby="awx-search"]';

    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true, isSearchable: true },
      { name: 'Bar', key: 'bar', isSortable: true, isSearchable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="foo"
        sortOrder="ascending"
        columns={multipleColumns}
        onSort={onSort}
      />
    );
    const sortDropdownToggle = toolbar.find(sortDropdownToggleSelector);
    expect(sortDropdownToggle.length).toBe(1);
    sortDropdownToggle.simulate('click');
    toolbar.update();
    const sortDropdownItems = toolbar.find(sortDropdownMenuItems).children();
    expect(sortDropdownItems.length).toBe(2);
    let searchDropdownToggle = toolbar.find(searchDropdownToggleSelector);
    expect(searchDropdownToggle.length).toBe(1);
    searchDropdownToggle.simulate('click');
    toolbar.update();
    let searchDropdownItems = toolbar.find(searchDropdownMenuItems).children();
    expect(searchDropdownItems.length).toBe(1);
    const mockedSortEvent = { target: { innerText: 'Bar' } };
    searchDropdownItems.at(0).simulate('click', mockedSortEvent);
    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="foo"
        sortOrder="descending"
        columns={multipleColumns}
        onSort={onSort}
      />
    );
    toolbar.update();

    const sortDropdownToggleDescending = toolbar.find(
      sortDropdownToggleSelector
    );
    expect(sortDropdownToggleDescending.length).toBe(1);
    sortDropdownToggleDescending.simulate('click');
    toolbar.update();

    const sortDropdownItemsDescending = toolbar
      .find(sortDropdownMenuItems)
      .children();
    expect(sortDropdownItemsDescending.length).toBe(2);
    sortDropdownToggleDescending.simulate('click'); // toggle close the sort dropdown

    const mockedSortEventDescending = { target: { innerText: 'Bar' } };
    sortDropdownItems.at(0).simulate('click', mockedSortEventDescending);
    toolbar.update();

    searchDropdownToggle = toolbar.find(searchDropdownToggleSelector);
    expect(searchDropdownToggle.length).toBe(1);
    searchDropdownToggle.simulate('click');
    toolbar.update();

    searchDropdownItems = toolbar.find(searchDropdownMenuItems).children();
    expect(searchDropdownItems.length).toBe(1);

    const mockedSearchEvent = { target: { innerText: 'Bar' } };
    searchDropdownItems.at(0).simulate('click', mockedSearchEvent);
  });

  test('it displays correct sort icon', () => {
    const downNumericIconSelector = 'SortNumericDownIcon';
    const upNumericIconSelector = 'SortNumericUpIcon';
    const downAlphaIconSelector = 'SortAlphaDownIcon';
    const upAlphaIconSelector = 'SortAlphaUpIcon';

    const numericColumns = [
      { name: 'ID', key: 'id', isSortable: true, isNumeric: true },
    ];
    const alphaColumns = [
      { name: 'Name', key: 'name', isSortable: true, isNumeric: false },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="id"
        sortOrder="descending"
        columns={numericColumns}
      />
    );

    const downNumericIcon = toolbar.find(downNumericIconSelector);
    expect(downNumericIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="id"
        sortOrder="ascending"
        columns={numericColumns}
      />
    );

    const upNumericIcon = toolbar.find(upNumericIconSelector);
    expect(upNumericIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="name"
        sortOrder="descending"
        columns={alphaColumns}
      />
    );

    const downAlphaIcon = toolbar.find(downAlphaIconSelector);
    expect(downAlphaIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={alphaColumns}
      />
    );

    const upAlphaIcon = toolbar.find(upAlphaIconSelector);
    expect(upAlphaIcon.length).toBe(1);
  });

  test('should render additionalControls', () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        columns={columns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        additionalControls={[
          <button key="1" id="test" type="button">
            click
          </button>,
        ]}
      />
    );

    const button = toolbar.find('#test');
    expect(button).toHaveLength(1);
    expect(button.text()).toEqual('click');
  });

  test('it triggers the expected callbacks', () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        isAllSelected
        showExpandCollapse
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={columns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        showSelectAll
      />
    );
    const checkbox = toolbar.find('Checkbox');
    expect(checkbox.prop('isChecked')).toBe(true);
  });
});
