import React from 'react';
import { act } from 'react-dom/test-utils';
import { shallow } from 'enzyme';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import Sort from './Sort';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useLocation: () => ({
    pathname: '/organizations',
  }),
}));

describe('<Sort />', () => {
  let sort;

  afterEach(() => {
    if (sort) {
      sort = null;
    }
  });

  test('should trigger onSort callback', () => {
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

  test('Changing dropdown correctly passes back new sort key', async () => {
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
    );
    act(() => wrapper.find('Dropdown').invoke('onToggle')(true));
    wrapper.update();
    await waitForElement(
      wrapper,
      'Dropdown',
      (el) => el.prop('isOpen') === true
    );
    act(() =>
      wrapper.find('li').at(0).prop('onClick')({ target: { innerText: 'Bar' } })
    );
    wrapper.update();
    expect(onSort).toBeCalledWith('bar', 'ascending');
  });

  test('should display numeric descending icon', () => {
    const qsConfigNumDown = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-id' },
      integerFields: ['page', 'page_size', 'id'],
    };
    const numericColumns = [{ name: 'ID', key: 'id' }];

    const wrapper = shallow(
      <Sort
        qsConfig={qsConfigNumDown}
        columns={numericColumns}
        onSort={jest.fn()}
      />
    );

    expect(wrapper.find('SortNumericDownAltIcon')).toHaveLength(1);
  });

  test('should display numeric ascending icon', () => {
    const qsConfigNumUp = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'id' },
      integerFields: ['page', 'page_size', 'id'],
    };
    const numericColumns = [{ name: 'ID', key: 'id' }];

    const wrapper = shallow(
      <Sort
        qsConfig={qsConfigNumUp}
        columns={numericColumns}
        onSort={jest.fn()}
      />
    );

    expect(wrapper.find('SortNumericDownIcon')).toHaveLength(1);
  });

  test('should display alphanumeric descending icon', () => {
    const qsConfigAlphaDown = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-name' },
      integerFields: ['page', 'page_size'],
    };
    const alphaColumns = [{ name: 'Name', key: 'name' }];

    const wrapper = shallow(
      <Sort
        qsConfig={qsConfigAlphaDown}
        columns={alphaColumns}
        onSort={jest.fn()}
      />
    );

    expect(wrapper.find('SortAlphaDownAltIcon')).toHaveLength(1);
  });

  test('should display alphanumeric ascending icon', () => {
    const qsConfigAlphaDown = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: 'name' },
      integerFields: ['page', 'page_size'],
    };
    const alphaColumns = [{ name: 'Name', key: 'name' }];

    const wrapper = shallow(
      <Sort
        qsConfig={qsConfigAlphaDown}
        columns={alphaColumns}
        onSort={jest.fn()}
      />
    );

    expect(wrapper.find('SortAlphaDownIcon')).toHaveLength(1);
  });
});
