import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationAccess from '../../../../../src/pages/Organizations/screens/Organization/OrganizationAccess';

describe('<OrganizationAccess />', () => {
  const organization = {
    id: 1,
    name: 'Default'
  };
  test('initially renders succesfully', () => {
    mountWithContexts(<OrganizationAccess organization={organization} />);
  });

  test('passed methods as props are called appropriately', async () => {
    const mockAPIAccessList = {
      foo: 'bar',
    };
    const mockResponse = {
      status: 'success',
    };
    const wrapper = mountWithContexts(<OrganizationAccess organization={organization} />,
      { context: { network: {
        api: {
          getOrganizationAccessList: () => Promise.resolve(mockAPIAccessList),
          disassociate: () => Promise.resolve(mockResponse)
        },
        handleHttpError: () => {}
      } } }).find('OrganizationAccess');
    const accessList = await wrapper.instance().getOrgAccessList();
    expect(accessList).toEqual(mockAPIAccessList);
    const resp = await wrapper.instance().removeRole(2, 3, 'users');
    expect(resp).toEqual(mockResponse);
  });
});
