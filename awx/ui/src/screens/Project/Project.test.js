import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI, ProjectsAPI } from 'api';
import mockOrganization from 'util/data.organization.json';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockDetails from './data.project.json';
import Project from './Project';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    pathname: '/projects/1/details',
    url: '/projects/1',
  }),
  useParams: () => ({ id: 1 }),
}));

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};

async function getOrganizations() {
  return {
    count: 1,
    next: null,
    previous: null,
    data: {
      results: [mockOrganization],
    },
  };
}

describe('<Project />', () => {
  let wrapper;

  beforeEach(() => {
    OrganizationsAPI.read = jest.fn();
    ProjectsAPI.readDetail = jest.fn();
    ProjectsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    OrganizationsAPI.read.mockImplementation(getOrganizations);
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      mountWithContexts(<Project setBreadcrumb={() => {}} me={mockMe} />);
    });
  });

  test('notifications tab shown for admins', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Project setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item-text',
      (el) => el.length === 6
    );
    expect(tabs.at(4).text()).toEqual('Notifications');
  });

  test('notifications tab hidden with reduced permissions', async () => {
    OrganizationsAPI.read = async () => ({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Project setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item-text',
      (el) => el.length === 5
    );
    tabs.forEach((tab) => expect(tab.text()).not.toEqual('Notifications'));
  });

  test('schedules tab shown for scm based projects.', async () => {
    OrganizationsAPI.read = async () => ({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Project setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      (el) => el.length === 5
    );
    expect(tabs.at(4).text()).toEqual('Schedules');
  });

  test('schedules tab hidden for manual projects.', async () => {
    const manualDetails = Object.assign(mockDetails, { scm_type: '' });
    ProjectsAPI.readDetail = async () => ({ data: manualDetails });
    OrganizationsAPI.read = async () => ({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Project setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      (el) => el.length === 4
    );
    tabs.forEach((tab) => expect(tab.text()).not.toEqual('Schedules'));
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/projects/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Project setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/projects/1/foobar',
                  path: '/project/1/foobar',
                },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
