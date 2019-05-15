import React from 'react';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../../../../enzymeHelpers';
import { sleep } from '../../../../testUtils';
import OrganizationTeams, { _OrganizationTeams } from '../../../../../src/pages/Organizations/screens/Organization/OrganizationTeams';

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
        handleHttpError={() => {}}
      />
    );
  });

  test('should load teams on mount', () => {
    const readOrganizationTeamsList = jest.fn(() => Promise.resolve(listData));
    mountWithContexts(
      <OrganizationTeams
        id={1}
        searchString=""
      />, { context: {
        network: { api: { readOrganizationTeamsList }, handleHttpError: () => {} } }
      }
    ).find('OrganizationTeams');
    expect(readOrganizationTeamsList).toHaveBeenCalledWith(1, {
      page: 1,
      page_size: 5,
      order_by: 'name',
    });
  });

  test('should pass fetched teams to PaginatedDatalist', async () => {
    const readOrganizationTeamsList = jest.fn(() => Promise.resolve(listData));
    const wrapper = mountWithContexts(
      <OrganizationTeams
        id={1}
        searchString=""
      />, { context: {
        network: { api: { readOrganizationTeamsList }, handleHttpError: () => {} } }
      }
    );

    await sleep(0);
    wrapper.update();

    const list = wrapper.find('PaginatedDataList');
    expect(list.prop('items')).toEqual(listData.data.results);
    expect(list.prop('itemCount')).toEqual(listData.data.count);
    expect(list.prop('qsConfig')).toEqual({
      namespace: 'team',
      defaultParams: {
        page: 1,
        page_size: 5,
        order_by: 'name',
      },
      integerFields: ['page', 'page_size'],
    });
  });
});
