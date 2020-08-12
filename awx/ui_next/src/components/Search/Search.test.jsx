import React from 'react';
import { Toolbar, ToolbarContent } from '@patternfly/react-core';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Search from './Search';

describe('<Search />', () => {
  let search;

  const QS_CONFIG = {
    namespace: 'organization',
    dateFields: ['modified', 'created'],
    defaultParams: { page: 1, page_size: 5, order_by: 'name' },
    integerFields: ['page', 'page_size'],
  };

  afterEach(() => {
    if (search) {
      search = null;
    }
  });

  test('it triggers the expected callbacks', () => {
    const columns = [{ name: 'Name', key: 'name__icontains', isDefault: true }];

    const searchBtn = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';

    const onSearch = jest.fn();

    search = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onSearch={onSearch}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>
    );

    search.find(searchTextInput).instance().value = 'test-321';
    search.find(searchTextInput).simulate('change');
    search.find(searchBtn).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('changing key select updates which key is called for onSearch', () => {
    const searchButton = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const columns = [
      { name: 'Name', key: 'name__icontains', isDefault: true },
      { name: 'Description', key: 'description__icontains' },
    ];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onSearch={onSearch}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>
    );

    act(() => {
      wrapper
        .find('Select[aria-label="Simple key select"]')
        .invoke('onSelect')({ target: { innerText: 'Description' } });
    });
    wrapper.update();
    wrapper.find(searchTextInput).instance().value = 'test-321';
    wrapper.find(searchTextInput).simulate('change');
    wrapper.find(searchButton).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('description__icontains', 'test-321');
  });

  test('changing key select to and from advanced causes onShowAdvancedSearch callback to be invoked', () => {
    const columns = [
      { name: 'Name', key: 'name__icontains', isDefault: true },
      { name: 'Description', key: 'description__icontains' },
      { name: 'Advanced', key: 'advanced' },
    ];
    const onSearch = jest.fn();
    const onShowAdvancedSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onSearch={onSearch}
            onShowAdvancedSearch={onShowAdvancedSearch}
          />
        </ToolbarContent>
      </Toolbar>
    );

    act(() => {
      wrapper
        .find('Select[aria-label="Simple key select"]')
        .invoke('onSelect')({ target: { innerText: 'Advanced' } });
    });
    wrapper.update();
    expect(onShowAdvancedSearch).toHaveBeenCalledTimes(1);
    expect(onShowAdvancedSearch).toBeCalledWith(true);
    jest.clearAllMocks();
    act(() => {
      wrapper
        .find('Select[aria-label="Simple key select"]')
        .invoke('onSelect')({ target: { innerText: 'Description' } });
    });
    wrapper.update();
    expect(onShowAdvancedSearch).toHaveBeenCalledTimes(1);
    expect(onShowAdvancedSearch).toBeCalledWith(false);
  });

  test('attempt to search with empty string', () => {
    const searchButton = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const columns = [{ name: 'Name', key: 'name__icontains', isDefault: true }];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onSearch={onSearch}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>
    );

    wrapper.find(searchTextInput).instance().value = '';
    wrapper.find(searchTextInput).simulate('change');
    wrapper.find(searchButton).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(0);
  });

  test('search with a valid string', () => {
    const searchButton = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    const columns = [{ name: 'Name', key: 'name__icontains', isDefault: true }];
    const onSearch = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onSearch={onSearch}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>
    );

    wrapper.find(searchTextInput).instance().value = 'test-321';
    wrapper.find(searchTextInput).simulate('change');
    wrapper.find(searchButton).simulate('click');

    expect(onSearch).toHaveBeenCalledTimes(1);
    expect(onSearch).toBeCalledWith('name__icontains', 'test-321');
  });

  test('filter keys are properly labeled', () => {
    const columns = [
      { name: 'Name', key: 'name__icontains', isDefault: true },
      { name: 'Type', key: 'or__scm_type', options: [['foo', 'Foo Bar!']] },
      { name: 'Description', key: 'description' },
    ];
    const query =
      '?organization.or__scm_type=foo&organization.name__icontains=bar&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/${query}`],
    });
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>,
      { context: { router: { history } } }
    );
    const typeFilterWrapper = wrapper.find(
      'ToolbarFilter[categoryName="Type (or__scm_type)"]'
    );
    expect(typeFilterWrapper.prop('chips')[0].key).toEqual('or__scm_type:foo');
    const nameFilterWrapper = wrapper.find(
      'ToolbarFilter[categoryName="Name (name__icontains)"]'
    );
    expect(nameFilterWrapper.prop('chips')[0].key).toEqual(
      'name__icontains:bar'
    );
  });

  test('should test handle remove of option-based key', async () => {
    const qsConfigNew = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-type' },
      integerFields: [],
    };
    const columns = [
      {
        name: 'type',
        key: 'type',
        options: [['foo', 'Foo Bar!']],
        isDefault: true,
      },
    ];
    const query = '?item.or__type=foo&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const onRemove = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${qsConfigNew.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={qsConfigNew}
            columns={columns}
            onRemove={onRemove}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>,
      { context: { router: { history } } }
    );
    expect(history.location.search).toEqual(query);
    // click remove button on chip
    await act(async () => {
      wrapper
        .find('.pf-c-chip button[aria-label="close"]')
        .at(0)
        .simulate('click');
    });
    expect(onRemove).toBeCalledWith('or__type', 'foo');
  });

  test('should test handle remove of option-based with empty string value', async () => {
    const qsConfigNew = {
      namespace: 'item',
      defaultParams: { page: 1, page_size: 5, order_by: '-type' },
      integerFields: [],
    };
    const columns = [
      {
        name: 'type',
        key: 'type',
        options: [['', 'manual']],
        isDefault: true,
      },
    ];
    const query = '?item.or__type=&item.page_size=10';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/1/teams${query}`],
    });
    const onRemove = jest.fn();
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${qsConfigNew.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={qsConfigNew}
            columns={columns}
            onRemove={onRemove}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>,
      { context: { router: { history } } }
    );
    expect(history.location.search).toEqual(query);
    // click remove button on chip
    await act(async () => {
      wrapper
        .find('.pf-c-chip button[aria-label="close"]')
        .at(0)
        .simulate('click');
    });
    expect(onRemove).toBeCalledWith('or__type', '');
  });

  test("ToolbarFilter added for any key that doesn't have search column", () => {
    const columns = [
      { name: 'Name', key: 'name__icontains', isDefault: true },
      { name: 'Type', key: 'or__scm_type', options: [['foo', 'Foo Bar!']] },
      { name: 'Description', key: 'description' },
    ];
    const query =
      '?organization.or__scm_type=foo&organization.name__icontains=bar&organization.name__exact=baz&item.page_size=10&organization.foo=bar';
    const history = createMemoryHistory({
      initialEntries: [`/organizations/${query}`],
    });
    const wrapper = mountWithContexts(
      <Toolbar
        id={`${QS_CONFIG.namespace}-list-toolbar`}
        clearAllFilters={() => {}}
        collapseListedFiltersBreakpoint="lg"
      >
        <ToolbarContent>
          <Search
            qsConfig={QS_CONFIG}
            columns={columns}
            onShowAdvancedSearch={jest.fn}
          />
        </ToolbarContent>
      </Toolbar>,
      { context: { router: { history } } }
    );
    const nameExactFilterWrapper = wrapper.find(
      'ToolbarFilter[categoryName="name__exact"]'
    );
    expect(nameExactFilterWrapper.prop('chips')[0].key).toEqual(
      'name__exact:baz'
    );
    const fooFilterWrapper = wrapper.find('ToolbarFilter[categoryName="foo"]');
    expect(fooFilterWrapper.prop('chips')[0].key).toEqual('foo:bar');
  });
});
