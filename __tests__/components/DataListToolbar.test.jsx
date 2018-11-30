import React from 'react';
import { mount } from 'enzyme';
import DataListToolbar from '../../src/components/DataListToolbar';

describe('<DataListToolbar />', () => {
  const columns = [{ name: 'Name', key: 'name', isSortable: true }];
  let toolbar;

  afterEach(() => {
    if (toolbar) {
      toolbar.unmount();
      toolbar = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const search = 'button[aria-label="Search"]';
    const searchTextInput = 'input[aria-label="search text input"]';
    const selectAll = 'input[aria-label="Select all"]';
    const sort = 'button[aria-label="Sort"]';

    const onSearch = jest.fn();
    const onSort = jest.fn();
    const onSelectAll = jest.fn();

    toolbar = mount(
      <DataListToolbar
        isAllSelected={false}
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={columns}
        onSearch={onSearch}
        onSort={onSort}
        onSelectAll={onSelectAll}
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
    expect(onSearch).toBeCalledWith('test-321');
  });
});
