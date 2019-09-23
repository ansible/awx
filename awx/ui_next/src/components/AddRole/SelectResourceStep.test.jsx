import React from 'react';
import { createMemoryHistory } from 'history';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { sleep } from '../../../testUtils/testUtils';
import SelectResourceStep from './SelectResourceStep';

describe('<SelectResourceStep />', () => {
  const columns = [
    { name: 'Username', key: 'username', isSortable: true, isSearchable: true },
  ];
  afterEach(() => {
    jest.restoreAllMocks();
  });
  test('initially renders without crashing', () => {
    shallow(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={() => {}}
        sortedColumnKey="username"
      />
    );
  });

  test('fetches resources on mount', async () => {
    const handleSearch = jest.fn().mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo', url: 'item/1' },
          { id: 2, username: 'bar', url: 'item/2' },
        ],
      },
    });
    mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={handleSearch}
        sortedColumnKey="username"
      />
    );
    expect(handleSearch).toHaveBeenCalledWith({
      order_by: 'username',
      page: 1,
      page_size: 5,
    });
  });

  test('readResourceList properly adds rows to state', async () => {
    const selectedResourceRows = [{ id: 1, username: 'foo', url: 'item/1' }];
    const handleSearch = jest.fn().mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo', url: 'item/1' },
          { id: 2, username: 'bar', url: 'item/2' },
        ],
      },
    });
    const history = createMemoryHistory({
      initialEntries: [
        '/organizations/1/access?resource.page=1&resource.order_by=-username',
      ],
    });
    const wrapper = await mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={handleSearch}
        selectedResourceRows={selectedResourceRows}
        sortedColumnKey="username"
      />,
      {
        context: { router: { history, route: { location: history.location } } },
      }
    ).find('SelectResourceStep');
    await wrapper.instance().readResourceList();
    expect(handleSearch).toHaveBeenCalledWith({
      order_by: '-username',
      page: 1,
      page_size: 5,
    });
    expect(wrapper.state('resources')).toEqual([
      { id: 1, username: 'foo', url: 'item/1' },
      { id: 2, username: 'bar', url: 'item/2' },
    ]);
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
    const wrapper = mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={handleRowClick}
        onSearch={() => ({ data })}
        selectedResourceRows={[]}
        sortedColumnKey="username"
      />
    );
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
