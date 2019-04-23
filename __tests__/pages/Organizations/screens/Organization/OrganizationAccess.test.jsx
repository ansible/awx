import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import OrganizationAccess from '../../../../../src/pages/Organizations/screens/Organization/OrganizationAccess';

describe('<OrganizationAccess />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<OrganizationAccess />);
  });

  test('passed methods as props are called appropriately', async () => {
    const mockAPIAccessList = {
      foo: 'bar',
    };
    const mockResponse = {
      status: 'success',
    };
    const wrapper = mountWithContexts(<OrganizationAccess />, { context: { network: {
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
