import React from 'react';
import { act } from 'react-dom/test-utils';

import { shallow } from 'enzyme';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { sleep } from '../../../testUtils/testUtils';
import SelectResourceStep from './SelectResourceStep';

describe('<SelectResourceStep />', () => {
  const searchColumns = [
    {
      name: 'Username',
      key: 'username__icontains',
      isDefault: true,
    },
  ];

  const sortColumns = [
    {
      name: 'Username',
      key: 'username',
    },
  ];
  afterEach(() => {
    jest.restoreAllMocks();
  });
  test('initially renders without crashing', () => {
    shallow(
      <SelectResourceStep
        searchColumns={searchColumns}
        sortColumns={sortColumns}
        displayKey="username"
        onRowClick={() => {}}
        fetchItems={() => {}}
        fetchOptions={() => {}}
      />
    );
  });

  test('fetches resources on mount and adds items to list', async () => {
    const handleSearch = jest.fn().mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo', url: 'item/1' },
          { id: 2, username: 'bar', url: 'item/2' },
        ],
      },
    });
    const options = jest.fn().mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SelectResourceStep
          searchColumns={searchColumns}
          sortColumns={sortColumns}
          displayKey="username"
          onRowClick={() => {}}
          fetchItems={handleSearch}
          fetchOptions={options}
        />
      );
    });
    expect(handleSearch).toHaveBeenCalledWith({
      order_by: 'username',
      page: 1,
      page_size: 5,
    });
    waitForElement(wrapper, 'CheckBoxListItem', el => el.length === 2);
  });

  test('clicking on row fires callback with correct params', async () => {
    const handleRowClick = jest.fn();
    const data = {
      count: 2,
      results: [
        { id: 1, username: 'foo', url: 'item/1' },
        { id: 2, username: 'bar', url: 'item/2' },
      ],
    };
    const options = jest.fn().mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SelectResourceStep
          searchColumns={searchColumns}
          sortColumns={sortColumns}
          displayKey="username"
          onRowClick={handleRowClick}
          fetchItems={() => ({ data })}
          fetchOptions={options}
          selectedResourceRows={[]}
        />
      );
    });
    await sleep(0);
    wrapper.update();
    const checkboxListItemWrapper = wrapper.find('CheckboxListItem');
    expect(checkboxListItemWrapper.length).toBe(2);

    checkboxListItemWrapper
      .first()
      .find('input[type="checkbox"]')
      .simulate('change', { target: { checked: true } });
    expect(handleRowClick).toHaveBeenCalledWith(data.results[0]);
  });
});
