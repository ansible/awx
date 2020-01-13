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
    const qsConfig = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page', 'page_size'],
    };

    const columns = [
      {
        name: 'Name',
        key: 'name',
      },
    ];

    const sortBtn = 'button[aria-label="Sort"]';

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort qsConfig={qsConfig} columns={columns} onSort={onSort} />
    ).find('Sort');

    wrapper.find(sortBtn).simulate('click');

    expect(onSort).toHaveBeenCalledTimes(1);
    expect(onSort).toBeCalledWith('name', 'descending');
  });

  test('onSort properly passes back descending when ascending was passed as prop', () => {
    const qsConfig = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'foo' },
      integerFields: ['page', 'page_size'],
    };

    const columns = [
      {
        name: 'Foo',
        key: 'foo',
      },
      {
        name: 'Bar',
        key: 'bar',
      },
      {
        name: 'Bakery',
        key: 'bakery',
      },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort qsConfig={qsConfig} columns={columns} onSort={onSort} />
    ).find('Sort');
    const sortDropdownToggle = wrapper.find('Button');
    expect(sortDropdownToggle.length).toBe(1);
    sortDropdownToggle.simulate('click');
    expect(onSort).toHaveBeenCalledWith('foo', 'descending');
  });

  test('onSort properly passes back ascending when descending was passed as prop', () => {
    const qsConfig = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-foo' },
      integerFields: ['page', 'page_size'],
    };

    const columns = [
      {
        name: 'Foo',
        key: 'foo',
      },
      {
        name: 'Bar',
        key: 'bar',
      },
      {
        name: 'Bakery',
        key: 'bakery',
      },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort qsConfig={qsConfig} columns={columns} onSort={onSort} />
    ).find('Sort');
    const sortDropdownToggle = wrapper.find('Button');
    expect(sortDropdownToggle.length).toBe(1);
    sortDropdownToggle.simulate('click');
    expect(onSort).toHaveBeenCalledWith('foo', 'ascending');
  });

  test('Changing dropdown correctly passes back new sort key', () => {
    const qsConfig = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'foo' },
      integerFields: ['page', 'page_size'],
    };

    const columns = [
      {
        name: 'Foo',
        key: 'foo',
      },
      {
        name: 'Bar',
        key: 'bar',
      },
      {
        name: 'Bakery',
        key: 'bakery',
      },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort qsConfig={qsConfig} columns={columns} onSort={onSort} />
    ).find('Sort');

    wrapper.instance().handleDropdownSelect({ target: { innerText: 'Bar' } });
    expect(onSort).toBeCalledWith('bar', 'ascending');
  });

  test('Opening dropdown correctly updates state', () => {
    const qsConfig = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'foo' },
      integerFields: ['page', 'page_size'],
    };

    const columns = [
      {
        name: 'Foo',
        key: 'foo',
      },
      {
        name: 'Bar',
        key: 'bar',
      },
      {
        name: 'Bakery',
        key: 'bakery',
      },
    ];

    const onSort = jest.fn();

    const wrapper = mountWithContexts(
      <Sort qsConfig={qsConfig} columns={columns} onSort={onSort} />
    ).find('Sort');
    expect(wrapper.state('isSortDropdownOpen')).toEqual(false);
    wrapper.instance().handleDropdownToggle(true);
    expect(wrapper.state('isSortDropdownOpen')).toEqual(true);
  });

  test('It displays correct sort icon', () => {
    const forwardNumericIconSelector = 'SortNumericDownIcon';
    const reverseNumericIconSelector = 'SortNumericDownAltIcon';
    const forwardAlphaIconSelector = 'SortAlphaDownIcon';
    const reverseAlphaIconSelector = 'SortAlphaDownAltIcon';

    const qsConfigNumDown = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-id' },
      integerFields: ['page', 'page_size', 'id'],
    };
    const qsConfigNumUp = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'id' },
      integerFields: ['page', 'page_size', 'id'],
    };
    const qsConfigAlphaDown = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-name' },
      integerFields: ['page', 'page_size'],
    };
    const qsConfigAlphaUp = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page', 'page_size'],
    };

    const numericColumns = [{ name: 'ID', key: 'id' }];
    const alphaColumns = [{ name: 'Name', key: 'name' }];
    const onSort = jest.fn();

    sort = mountWithContexts(
      <Sort
        qsConfig={qsConfigNumDown}
        columns={numericColumns}
        onSort={onSort}
      />
    );

    const reverseNumericIcon = sort.find(reverseNumericIconSelector);
    expect(reverseNumericIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort qsConfig={qsConfigNumUp} columns={numericColumns} onSort={onSort} />
    );

    const forwardNumericIcon = sort.find(forwardNumericIconSelector);
    expect(forwardNumericIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort
        qsConfig={qsConfigAlphaDown}
        columns={alphaColumns}
        onSort={onSort}
      />
    );

    const reverseAlphaIcon = sort.find(reverseAlphaIconSelector);
    expect(reverseAlphaIcon.length).toBe(1);

    sort = mountWithContexts(
      <Sort qsConfig={qsConfigAlphaUp} columns={alphaColumns} onSort={onSort} />
    );

    const forwardAlphaIcon = sort.find(forwardAlphaIconSelector);
    expect(forwardAlphaIcon.length).toBe(1);
  });
});
