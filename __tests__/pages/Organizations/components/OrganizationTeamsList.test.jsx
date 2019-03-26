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
            onReadTeamsList={() => {}}
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
            onReadTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');

    setImmediate(() => {
      expect(wrapper.state().results).toEqual(mockData);
      done();
    });
  });

  test('handleSort being passed properly to DataListToolbar component', async (done) => {
    const handleSort = jest.spyOn(OrganizationTeamsList.prototype, 'handleSort');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            onReadTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');
    expect(handleSort).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update();
      rendered.find('button[aria-label="Sort"]').simulate('click');
      expect(handleSort).toHaveBeenCalled();
      done();
    });
  });

  test('handleSetPage calls readQueryParams and readOrganizationTeamsList ', () => {
    const spyQueryParams = jest.spyOn(OrganizationTeamsList.prototype, 'readQueryParams');
    const spyFetch = jest.spyOn(OrganizationTeamsList.prototype, 'readOrganizationTeamsList');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeamsList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/teams' }}
            onReadTeamsList={() => ({ data: { count: 1, results: mockData } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeamsList');
    wrapper.instance().handleSetPage(2, 10);
    expect(spyQueryParams).toHaveBeenCalled();
    expect(spyFetch).toHaveBeenCalled();
    wrapper.setState({ sortOrder: 'descending' });
    wrapper.instance().handleSetPage(3, 5);
    expect(spyQueryParams).toHaveBeenCalled();
    expect(spyFetch).toHaveBeenCalled();
    const queryParamCalls = spyQueryParams.mock.calls;
    // make sure last two readQueryParams calls
    // were called with the correct arguments
    expect(queryParamCalls[queryParamCalls.length - 2][0])
      .toEqual({ order_by: 'name', page: 2, page_size: 10 });
    expect(queryParamCalls[queryParamCalls.length - 1][0])
      .toEqual({ order_by: '-name', page: 3, page_size: 5 });
  });
});
