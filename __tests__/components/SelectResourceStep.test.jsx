import React from 'react';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../enzymeHelpers';
import SelectResourceStep from '../../src/components/AddRole/SelectResourceStep';

describe('<SelectResourceStep />', () => {
  const columns = [
    { name: 'Username', key: 'username', isSortable: true }
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
          { id: 1, username: 'foo' },
          { id: 2, username: 'bar' }
        ]
      }
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
      page_size: 5
    });
  });
  test('readResourceList properly adds rows to state', async () => {
    const selectedResourceRows = [
      {
        id: 1,
        username: 'foo'
      }
    ];
    const handleSearch = jest.fn().mockResolvedValue({
      data: {
        count: 2,
        results: [
          { id: 1, username: 'foo' },
          { id: 2, username: 'bar' }
        ]
      }
    });
    const wrapper = await mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={handleSearch}
        selectedResourceRows={selectedResourceRows}
        sortedColumnKey="username"
      />
    ).find('SelectResourceStep');
    await wrapper.instance().readResourceList({
      page: 1,
      order_by: '-username'
    });
    expect(handleSearch).toHaveBeenCalledWith({
      order_by: '-username',
      page: 1
    });
    expect(wrapper.state('resources')).toEqual([
      { id: 1, username: 'foo' },
      { id: 2, username: 'bar' }
    ]);
  });
  test('handleSetPage calls readResourceList with correct params', () => {
    const spy = jest.spyOn(SelectResourceStep.prototype, 'readResourceList');
    const wrapper = mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={() => {}}
        selectedResourceRows={[]}
        sortedColumnKey="username"
      />
    ).find('SelectResourceStep');
    wrapper.setState({ sortOrder: 'descending' });
    wrapper.instance().handleSetPage(2);
    expect(spy).toHaveBeenCalledWith({ page: 2, page_size: 5, order_by: '-username' });
    wrapper.setState({ sortOrder: 'ascending' });
    wrapper.instance().handleSetPage(2);
    expect(spy).toHaveBeenCalledWith({ page: 2, page_size: 5, order_by: 'username' });
  });
  test('handleSort calls readResourceList with correct params', () => {
    const spy = jest.spyOn(SelectResourceStep.prototype, 'readResourceList');
    const wrapper = mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={() => {}}
        onSearch={() => {}}
        selectedResourceRows={[]}
        sortedColumnKey="username"
      />
    ).find('SelectResourceStep');
    wrapper.instance().handleSort('username', 'descending');
    expect(spy).toHaveBeenCalledWith({ page: 1, page_size: 5, order_by: '-username' });
    wrapper.instance().handleSort('username', 'ascending');
    expect(spy).toHaveBeenCalledWith({ page: 1, page_size: 5, order_by: 'username' });
  });
  test('clicking on row fires callback with correct params', () => {
    const handleRowClick = jest.fn();
    const wrapper = mountWithContexts(
      <SelectResourceStep
        columns={columns}
        displayKey="username"
        onRowClick={handleRowClick}
        onSearch={() => {}}
        selectedResourceRows={[]}
        sortedColumnKey="username"
      />
    );
    const selectResourceStepWrapper = wrapper.find('SelectResourceStep');
    selectResourceStepWrapper.setState({
      resources: [
        { id: 1, username: 'foo' }
      ]
    });
    const checkboxListItemWrapper = wrapper.find('CheckboxListItem');
    expect(checkboxListItemWrapper.length).toBe(1);
    checkboxListItemWrapper.first().find('input[type="checkbox"]').simulate('change', { target: { checked: true } });
    expect(handleRowClick).toHaveBeenCalledWith({ id: 1, username: 'foo' });
  });
});
