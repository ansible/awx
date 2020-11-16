import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DataListToolbar from './DataListToolbar';
import AddDropDownButton from '../AddDropDownButton/AddDropDownButton';

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
  const onReplaceSearch = jest.fn();
  const onSort = jest.fn();
  const onSelectAll = jest.fn();

  test('it triggers the expected callbacks', () => {
    const searchColumns = [
      { name: 'Name', key: 'name__icontains', isDefault: true },
    ];
    const sortColumns = [{ name: 'Name', key: 'name' }];
    const search = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const selectAll = 'input[aria-label="Select all"]';
    const sort = 'button[aria-label="Sort"]';

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        isAllSelected={false}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        onSearch={onSearch}
        onReplaceSearch={onReplaceSearch}
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
    const searchDropdownToggleSelector =
      'Select[aria-label="Simple key select"] SelectToggle';
    const sortDropdownMenuItems =
      'DropdownMenu > ul[aria-labelledby="awx-sort"]';
    const searchDropdownMenuItems =
      'Select[aria-label="Simple key select"] SelectOption';

    const NEW_QS_CONFIG = {
      namespace: 'organization',
      dateFields: ['modified', 'created'],
      defaultParams: { page: 1, page_size: 5, order_by: 'foo' },
      integerFields: ['page', 'page_size'],
    };

    const searchColumns = [
      { name: 'Foo', key: 'foo', isDefault: true },
      { name: 'Bar', key: 'bar' },
    ];
    const sortColumns = [
      { name: 'Foo', key: 'foo' },
      { name: 'Bar', key: 'bar' },
      { name: 'Bakery', key: 'Bakery' },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={NEW_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
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
    expect(searchDropdownItems.length).toBe(2);
    const mockedSortEvent = { target: { innerText: 'Bar' } };
    searchDropdownItems.at(0).simulate('click', mockedSortEvent);
    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={NEW_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
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
    expect(searchDropdownItems.length).toBe(2);

    const mockedSearchEvent = { target: { innerText: 'Bar' } };
    searchDropdownItems.at(0).simulate('click', mockedSearchEvent);
  });

  test('it displays correct sort icon', () => {
    const NUM_QS_CONFIG = {
      namespace: 'organization',
      dateFields: ['modified', 'created'],
      defaultParams: { page: 1, page_size: 5, order_by: 'id' },
      integerFields: ['page', 'page_size', 'id'],
    };

    const NUM_DESC_QS_CONFIG = {
      namespace: 'organization',
      dateFields: ['modified', 'created'],
      defaultParams: { page: 1, page_size: 5, order_by: '-id' },
      integerFields: ['page', 'page_size', 'id'],
    };

    const ALPH_QS_CONFIG = {
      namespace: 'organization',
      dateFields: ['modified', 'created'],
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page', 'page_size', 'id'],
    };

    const ALPH_DESC_QS_CONFIG = {
      namespace: 'organization',
      dateFields: ['modified', 'created'],
      defaultParams: { page: 1, page_size: 5, order_by: '-name' },
      integerFields: ['page', 'page_size', 'id'],
    };

    const forwardNumericIconSelector = 'SortNumericDownIcon';
    const reverseNumericIconSelector = 'SortNumericDownAltIcon';
    const forwardAlphaIconSelector = 'SortAlphaDownIcon';
    const reverseAlphaIconSelector = 'SortAlphaDownAltIcon';

    const numericColumns = [{ name: 'ID', key: 'id' }];

    const alphaColumns = [{ name: 'Name', key: 'name' }];

    const searchColumns = [
      { name: 'Name', key: 'name', isDefault: true },
      { name: 'ID', key: 'id' },
    ];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={NUM_DESC_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={numericColumns}
      />
    );

    const reverseNumericIcon = toolbar.find(reverseNumericIconSelector);
    expect(reverseNumericIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={NUM_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={numericColumns}
      />
    );

    const forwardNumericIcon = toolbar.find(forwardNumericIconSelector);
    expect(forwardNumericIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={ALPH_DESC_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={alphaColumns}
      />
    );

    const reverseAlphaIcon = toolbar.find(reverseAlphaIconSelector);
    expect(reverseAlphaIcon.length).toBe(1);

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={ALPH_QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={alphaColumns}
      />
    );

    const forwardAlphaIcon = toolbar.find(forwardAlphaIconSelector);
    expect(forwardAlphaIcon.length).toBe(1);
  });

  test('should render additionalControls', () => {
    const searchColumns = [{ name: 'Name', key: 'name', isDefault: true }];
    const sortColumns = [{ name: 'Name', key: 'name' }];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        onSearch={onSearch}
        onReplaceSearch={onReplaceSearch}
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
    const searchColumns = [{ name: 'Name', key: 'name', isDefault: true }];
    const sortColumns = [{ name: 'Name', key: 'name' }];
    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        isAllSelected
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        onSearch={onSearch}
        onReplaceSearch={onReplaceSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        showSelectAll
      />
    );
    const checkbox = toolbar.find('Checkbox');
    expect(checkbox.prop('isChecked')).toBe(true);
  });

  test('always adds advanced item to search column array', () => {
    const searchColumns = [{ name: 'Name', key: 'name', isDefault: true }];
    const sortColumns = [{ name: 'Name', key: 'name' }];

    toolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        onSearch={onSearch}
        onReplaceSearch={onReplaceSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        additionalControls={[
          <button key="1" id="test" type="button">
            click
          </button>,
        ]}
      />
    );

    const search = toolbar.find('Search');
    expect(
      search.prop('columns').filter(col => col.key === 'advanced').length
    ).toBe(1);
  });

  test('should properly render toolbar buttons when in advanced search mode', async () => {
    const searchColumns = [{ name: 'Name', key: 'name', isDefault: true }];
    const sortColumns = [{ name: 'Name', key: 'name' }];

    const newToolbar = mountWithContexts(
      <DataListToolbar
        qsConfig={QS_CONFIG}
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        onSearch={onSearch}
        onReplaceSearch={onReplaceSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
        additionalControls={[
          <AddDropDownButton
            dropdownItems={[
              <div key="add container" aria-label="add container">
                Add Contaner
              </div>,
              <div key="add instance group" aria-label="add instance group">
                Add Instance Group
              </div>,
            ]}
          />,
        ]}
      />
    );
    act(() => newToolbar.find('Search').prop('onShowAdvancedSearch')(true));
    newToolbar.update();
    expect(newToolbar.find('KebabToggle').length).toBe(1);
    act(() => newToolbar.find('KebabToggle').prop('onToggle')(true));
    newToolbar.update();
    expect(newToolbar.find('div[aria-label="add container"]').length).toBe(1);
    expect(newToolbar.find('div[aria-label="add instance group"]').length).toBe(
      1
    );
  });
});
