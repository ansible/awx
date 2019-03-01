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

const mockGetOrganzationAccessList = jest.fn(() => (
  Promise.resolve(mockAPIAccessList)
));

const mockGetUserRoles = jest.fn(() => (
  Promise.resolve(mockAPIRoles)
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
          }}
        />
      </MemoryRouter>
    ).find('OrganizationAccess');
    const accessList = await wrapper.instance().getOrgAccessList();
    expect(accessList).toEqual(mockAPIAccessList);
    const userRoles = await wrapper.instance().getUserRoles();
    expect(userRoles).toEqual(mockAPIRoles);
  });
});
