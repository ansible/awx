import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockOrganization from '../../util/data.organization.json';
import Organization from './Organization';

jest.mock('../../api');

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

describe('<Organization />', () => {
  let wrapper;

  beforeAll(() => {
    OrganizationsAPI.readDetail.mockResolvedValue({ data: mockOrganization });
    OrganizationsAPI.readGalaxyCredentials.mockResolvedValue({
      data: {
        results: [],
      },
    });
  });

  test('initially renders succesfully', async () => {
    OrganizationsAPI.read.mockImplementation(getOrganizations);
    await act(async () => {
      mountWithContexts(<Organization setBreadcrumb={() => {}} me={mockMe} />);
    });
  });

  test('notifications tab shown for admins', async done => {
    OrganizationsAPI.read.mockImplementation(getOrganizations);

    await act(async () => {
      wrapper = mountWithContexts(
        <Organization setBreadcrumb={() => {}} me={mockMe} />
      );
    });

    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 5
    );
    expect(tabs.last().text()).toEqual('Notifications');
    wrapper.unmount();
    done();
  });

  test('notifications tab hidden with reduced permissions', async done => {
    OrganizationsAPI.read.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Organization setBreadcrumb={() => {}} me={mockMe} />
      );
    });

    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 4
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    wrapper.unmount();
    done();
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
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
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    wrapper.unmount();
  });
});
