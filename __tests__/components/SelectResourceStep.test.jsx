import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import SelectResourceStep from '../../src/components/AddRole/SelectResourceStep';

describe('<SelectResourceStep />', () => {
  const columns = [
    { name: 'Username', key: 'username', isSortable: true }
  ];
  afterEach(() => {
    jest.restoreAllMocks();
  });
  test('initially renders without crashing', () => {
    mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          defaultSearchParams={{
            is_superuser: false
          }}
          displayKey="username"
          onRowClick={jest.fn()}
          onSearch={jest.fn()}
          sortedColumnKey="username"
        />
      </I18nProvider>
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
    mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          defaultSearchParams={{
            is_superuser: false
          }}
          displayKey="username"
          onRowClick={jest.fn()}
          onSearch={handleSearch}
          sortedColumnKey="username"
        />
      </I18nProvider>
    );
    expect(handleSearch).toHaveBeenCalledWith({
      is_superuser: false,
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
    const wrapper = await mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          defaultSearchParams={{
            is_superuser: false
          }}
          displayKey="username"
          onRowClick={jest.fn()}
          onSearch={handleSearch}
          selectedResourceRows={selectedResourceRows}
          sortedColumnKey="username"
        />
      </I18nProvider>
    ).find('SelectResourceStep');
    await wrapper.instance().readResourceList({
      page: 1,
      order_by: '-username'
    });
    expect(handleSearch).toHaveBeenCalledWith({
      is_superuser: false,
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
    const wrapper = mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          displayKey="username"
          onRowClick={jest.fn()}
          onSearch={jest.fn()}
          selectedResourceRows={[]}
          sortedColumnKey="username"
        />
      </I18nProvider>
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
    const wrapper = mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          displayKey="username"
          onRowClick={jest.fn()}
          onSearch={jest.fn()}
          selectedResourceRows={[]}
          sortedColumnKey="username"
        />
      </I18nProvider>
    ).find('SelectResourceStep');
    wrapper.instance().handleSort('username', 'descending');
    expect(spy).toHaveBeenCalledWith({ page: 1, page_size: 5, order_by: '-username' });
    wrapper.instance().handleSort('username', 'ascending');
    expect(spy).toHaveBeenCalledWith({ page: 1, page_size: 5, order_by: 'username' });
  });
  test('clicking on row fires callback with correct params', () => {
    const handleRowClick = jest.fn();
    const wrapper = mount(
      <I18nProvider>
        <SelectResourceStep
          columns={columns}
          displayKey="username"
          onRowClick={handleRowClick}
          onSearch={jest.fn()}
          selectedResourceRows={[]}
          sortedColumnKey="username"
        />
      </I18nProvider>
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
