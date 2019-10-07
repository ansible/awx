import React from 'react';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockOrganization from '@util/data.organization.json';
import Organization from './Organization';

jest.mock('@api');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};

async function getOrganizations(params) {
  let results = [];
  if (params && params.role_level) {
    if (params.role_level === 'admin_role') {
      results = [mockOrganization];
    }
    if (params.role_level === 'auditor_role') {
      results = [mockOrganization];
    }
    if (params.role_level === 'notification_admin_role') {
      results = [mockOrganization];
    }
  }
  return {
    count: results.length,
    next: null,
    previous: null,
    data: { results },
  };
}

describe.only('<Organization />', () => {
  test('initially renders succesfully', () => {
    OrganizationsAPI.readDetail.mockResolvedValue({ data: mockOrganization });
    OrganizationsAPI.read.mockImplementation(getOrganizations);
    mountWithContexts(<Organization setBreadcrumb={() => {}} me={mockMe} />);
  });

  test('notifications tab shown for admins', async done => {
    OrganizationsAPI.readDetail.mockResolvedValue({ data: mockOrganization });
    OrganizationsAPI.read.mockImplementation(getOrganizations);

    const wrapper = mountWithContexts(
      <Organization setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 4
    );
    expect(tabs.last().text()).toEqual('Notifications');
    done();
  });

  test('notifications tab hidden with reduced permissions', async done => {
    OrganizationsAPI.readDetail.mockResolvedValue({ data: mockOrganization });
    OrganizationsAPI.read.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    const wrapper = mountWithContexts(
      <Organization setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 3
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    done();
  });

  test('should show content error when user attempts to navigate to erroneous route', async done => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/foobar'],
    });
    const wrapper = mountWithContexts(
      <Organization setBreadcrumb={() => {}} me={mockMe} />,
      {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/organizations/1/foobar',
                path: '/organizations/1/foobar',
              },
            },
          },
        },
      }
    );
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    done();
  });
});
