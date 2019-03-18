import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';

import OrganizationAccess from '../../../../../src/pages/Organizations/screens/Organization/OrganizationAccess';

const mockAPIAccessList = {
  foo: 'bar',
};

const mockGetOrganzationAccessList = () => Promise.resolve(mockAPIAccessList);

const mockResponse = {
  status: 'success',
};

const mockRemoveRole = () => Promise.resolve(mockResponse);

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
            disassociate: mockRemoveRole
          }}
        />
      </MemoryRouter>
    ).find('OrganizationAccess');
    const accessList = await wrapper.instance().getOrgAccessList();
    expect(accessList).toEqual(mockAPIAccessList);
    const resp = await wrapper.instance().removeRole(2, 3, 'users');
    expect(resp).toEqual(mockResponse);
  });
});
