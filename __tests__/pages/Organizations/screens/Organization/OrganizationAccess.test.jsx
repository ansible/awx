import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';

import OrganizationAccess from '../../../../../src/pages/Organizations/screens/Organization/OrganizationAccess';

const mockAPIAccessList = {
  foo: 'bar',
};
const mockAPIRoles = {
  bar: 'baz',
};
const mockAPITeams = {
  qux: 'quux',
};
const mockAPITeamRoles = {
  quuz: 'quuz',
};

const mockGetOrganzationAccessList = jest.fn(() => (
  Promise.resolve(mockAPIAccessList)
));

const mockGetUserRoles = jest.fn(() => (
  Promise.resolve(mockAPIRoles)
));

const mockGetUserTeams = jest.fn(() => (
  Promise.resolve(mockAPITeams)
));

const mockGetTeamRoles = jest.fn(() => (
  Promise.resolve(mockAPITeamRoles)
));

describe('<OrganizationAccess />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <OrganizationAccess
          match={{ path: '/organizations/:id/access', url: '/organizations/1/access', params: { id: 1 } }}
          location={{ search: '', pathname: '/organizations/1/access' }}
          params={{}}
          api={{
            getOrganzationAccessList: jest.fn(),
            getUserRoles: jest.fn(),
            getUserTeams: jest.fn(),
            getTeamRoles: jest.fn(),
          }}
        />
      </MemoryRouter>
    );
  });

  test('passed methods as props are called appropriately', async () => {
    const wrapper = mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <OrganizationAccess
          match={{ path: '/organizations/:id/access', url: '/organizations/1/access', params: { id: 1 } }}
          location={{ search: '', pathname: '/organizations/1/access' }}
          params={{}}
          api={{
            getOrganzationAccessList: mockGetOrganzationAccessList,
            getUserRoles: mockGetUserRoles,
            getUserTeams: mockGetUserTeams,
            getTeamRoles: mockGetTeamRoles,
          }}
        />
      </MemoryRouter>
    ).find('OrganizationAccess');
    const accessList = await wrapper.instance().getOrgAccessList();
    expect(accessList).toEqual(mockAPIAccessList);
    const userRoles = await wrapper.instance().getUserRoles();
    expect(userRoles).toEqual(mockAPIRoles);
    const userTeams = await wrapper.instance().getUserTeams();
    expect(userTeams).toEqual(mockAPITeams);
    const teamRoles = await wrapper.instance().getTeamRoles();
    expect(teamRoles).toEqual(mockAPITeamRoles);
  });
});
