import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Sort from './Sort';

describe('<Sort />', () => {
  let sort;

  afterEach(() => {
    if (sort) {
      sort = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const columns = [
      { name: 'Name', key: 'name', isSortable: true, isSearchable: true },
    ];

    const sortBtn = 'button[aria-label="Sort"]';

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={columns}
        onSort={onSort}
      />
    ).find('Sort');

    wrapper.find(sortBtn).simulate('click');

    expect(onSort).toHaveBeenCalledTimes(1);
    expect(onSort).toBeCalledWith('name', 'descending');
  });

  test('onSort properly passes back descending when ascending was passed as prop', () => {
    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true },
      { name: 'Bar', key: 'bar', isSortable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort
        sortedColumnKey="foo"
        sortOrder="ascending"
        columns={multipleColumns}
        onSort={onSort}
      />
    ).find('Sort');
    const sortDropdownToggle = wrapper.find('Button');
    expect(sortDropdownToggle.length).toBe(1);
    sortDropdownToggle.simulate('click');
    expect(onSort).toHaveBeenCalledWith('foo', 'descending');
  });

  test('onSort properly passes back ascending when descending was passed as prop', () => {
    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true },
      { name: 'Bar', key: 'bar', isSortable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort
        sortedColumnKey="foo"
        sortOrder="descending"
        columns={multipleColumns}
        onSort={onSort}
      />
    ).find('Sort');
    const sortDropdownToggle = wrapper.find('Button');
    expect(sortDropdownToggle.length).toBe(1);
    sortDropdownToggle.simulate('click');
    expect(onSort).toHaveBeenCalledWith('foo', 'ascending');
  });

  test('Changing dropdown correctly passes back new sort key', () => {
    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true },
      { name: 'Bar', key: 'bar', isSortable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort
        sortedColumnKey="foo"
        sortOrder="ascending"
        columns={multipleColumns}
        onSort={onSort}
      />
    ).find('Sort');

    wrapper.instance().handleDropdownSelect({ target: { innerText: 'Bar' } });
    expect(onSort).toBeCalledWith('bar', 'ascending');
  });

  test('Opening dropdown correctly updates state', () => {
    const multipleColumns = [
      { name: 'Foo', key: 'foo', isSortable: true },
      { name: 'Bar', key: 'bar', isSortable: true },
      { name: 'Bakery', key: 'bakery', isSortable: true },
      { name: 'Baz', key: 'baz' },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort
        sortedColumnKey="foo"
        sortOrder="ascending"
        columns={multipleColumns}
        onSort={onSort}
      />
    ).find('Sort');
    expect(wrapper.state('isSortDropdownOpen')).toEqual(false);
    wrapper.instance().handleDropdownToggle(true);
    expect(wrapper.state('isSortDropdownOpen')).toEqual(true);
  });

  test('It displays correct sort icon', () => {
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
    const onSort = jest.fn();

    sort = mountWithContexts(
      <Sort
        sortedColumnKey="id"
        sortOrder="descending"
        columns={numericColumns}
        onSort={onSort}
      />
    );

    const downNumericIcon = sort.find(downNumericIconSelector);
    expect(downNumericIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort
        sortedColumnKey="id"
        sortOrder="ascending"
        columns={numericColumns}
        onSort={onSort}
      />
    );

    const upNumericIcon = sort.find(upNumericIconSelector);
    expect(upNumericIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort
        sortedColumnKey="name"
        sortOrder="descending"
        columns={alphaColumns}
        onSort={onSort}
      />
    );

    const downAlphaIcon = sort.find(downAlphaIconSelector);
    expect(downAlphaIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort
        sortedColumnKey="name"
        sortOrder="ascending"
        columns={alphaColumns}
        onSort={onSort}
      />
    );

    const upAlphaIcon = sort.find(upAlphaIconSelector);
    expect(upAlphaIcon.length).toBe(1);
  });
});
