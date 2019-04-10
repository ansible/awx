import React from 'react';
import { mount, shallow } from 'enzyme';
import { MemoryRouter, Router } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { createMemoryHistory } from 'history';
import { sleep } from '../../../../testUtils';
import OrganizationTeams, { _OrganizationTeams } from '../../../../../src/pages/Organizations/screens/Organization/OrganizationTeams';
import OrganizationTeamsList from '../../../../../src/pages/Organizations/components/OrganizationTeamsList';

const listData = {
  data: {
    count: 7,
    results: [
      { id: 1, name: 'one', url: '/org/team/1' },
      { id: 2, name: 'two', url: '/org/team/2' },
      { id: 3, name: 'three', url: '/org/team/3' },
      { id: 4, name: 'four', url: '/org/team/4' },
      { id: 5, name: 'five', url: '/org/team/5' },
    ]
  }
};

describe('<OrganizationTeams />', () => {
  test('renders succesfully', () => {
    shallow(
      <_OrganizationTeams
        id={1}
        searchString=""
        location={{ search: '', pathname: '/organizations/1/teams' }}
        api={{
          readOrganizationTeamsList: jest.fn(),
        }}
      />
    );
  });

  test('should load teams on mount', () => {
    const readOrganizationTeamsList = jest.fn(() => Promise.resolve(listData));
    mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationTeams
            id={1}
            searchString=""
            api={{ readOrganizationTeamsList }}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('OrganizationTeams');
    expect(readOrganizationTeamsList).toHaveBeenCalledWith(1, {
      page: 1,
      page_size: 5,
      order_by: 'name',
    });
  });

  test('should pass fetched teams to list component', async () => {
    const readOrganizationTeamsList = jest.fn(() => Promise.resolve(listData));
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <OrganizationTeams
            id={1}
            searchString=""
            api={{ readOrganizationTeamsList }}
          />
        </MemoryRouter>
      </I18nProvider>
    );

    await sleep(0);
    wrapper.update();

    const list = wrapper.find('OrganizationTeamsList');
    expect(list.prop('teams')).toEqual(listData.data.results);
    expect(list.prop('itemCount')).toEqual(listData.data.count);
    expect(list.prop('queryParams')).toEqual({
      page: 1,
      page_size: 5,
      order_by: 'name',
    });
  });

  test('should pass queryParams to OrganizationTeamsList', async () => {
    const page1Data = listData;
    const page2Data = {
      data: {
        count: 7,
        results: [
          { id: 6, name: 'six', url: '/org/team/6' },
          { id: 7, name: 'seven', url: '/org/team/7' },
        ]
      }
    };
    const readOrganizationTeamsList = jest.fn();
    readOrganizationTeamsList.mockReturnValueOnce(page1Data);
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/teams'],
    });
    const wrapper = mount(
      <Router history={history}>
        <I18nProvider>
          <OrganizationTeams
            id={1}
            searchString=""
            api={{ readOrganizationTeamsList }}
          />
        </I18nProvider>
      </Router>
    );

    await sleep(0);
    wrapper.update();

    const list = wrapper.find(OrganizationTeamsList);
    expect(list.prop('queryParams')).toEqual({
      page: 1,
      page_size: 5,
      order_by: 'name',
    });

    readOrganizationTeamsList.mockReturnValueOnce(page2Data);
    history.push('/organizations/1/teams?page=2');
    wrapper.setProps({ history });

    await sleep(0);
    wrapper.update();
    const list2 = wrapper.find(OrganizationTeamsList);
    expect(list2.prop('queryParams')).toEqual({
      page: 2,
      page_size: 5,
      order_by: 'name',
    });
  });
});
