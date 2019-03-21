import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import OrganizationTeamsList from '../../../../src/pages/Organizations/components/OrganizationTeamsList';

const mockData = [
  {
    id: 1,
    name: 'boo',
    url: '/foo/bar/'
  }
];

describe('<OrganizationTeamsList />', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initially renders succesfully', () => {
    mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '1' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            getTeamsList={() => {}}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });

  test('api response data passed to component gets set to state properly', (done) => {
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            getTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');

    setImmediate(() => {
      expect(wrapper.state().results).toEqual(mockData);
      done();
    });
  });

  test('onSort being passed properly to DataListToolbar component', async (done) => {
    const onSort = jest.spyOn(OrganizationTeamsList.prototype, 'onSort');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            getTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');
    expect(onSort).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update();
      rendered.find('button[aria-label="Sort"]').simulate('click');
      expect(onSort).toHaveBeenCalled();
      done();
    });
  });

  test('onSetPage calls getQueryParams fetchOrgTeamsList ', () => {
    const spyQueryParams = jest.spyOn(OrganizationTeamsList.prototype, 'getQueryParams');
    const spyFetch = jest.spyOn(OrganizationTeamsList.prototype, 'fetchOrgTeamsList');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            getTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');
    wrapper.instance().onSetPage(2, 10);
    expect(spyQueryParams).toHaveBeenCalled();
    expect(spyFetch).toHaveBeenCalled();
    wrapper.setState({ sortOrder: 'descending' });
    wrapper.instance().onSetPage(3, 5);
    expect(spyQueryParams).toHaveBeenCalled();
    expect(spyFetch).toHaveBeenCalled();
    const queryParamCalls = spyQueryParams.mock.calls;
    // make sure last two getQueryParams calls
    // were called with the correct arguments
    expect(queryParamCalls[queryParamCalls.length - 2][0])
      .toEqual({ order_by: 'name', page: 2, page_size: 10 });
    expect(queryParamCalls[queryParamCalls.length - 1][0])
      .toEqual({ order_by: '-name', page: 3, page_size: 5 });
  });
});
