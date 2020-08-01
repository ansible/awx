import React from 'react';
import { createMemoryHistory } from 'history';
import { OrganizationsAPI, ProjectsAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockOrganization from '../../util/data.organization.json';
import mockDetails from './data.project.json';
import Project from './Project';

jest.mock('../../api');

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
  test('initially renders succesfully', () => {
    ProjectsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    OrganizationsAPI.read.mockImplementation(getOrganizations);
    mountWithContexts(<Project setBreadcrumb={() => {}} me={mockMe} />);
  });

  test('notifications tab shown for admins', async done => {
    ProjectsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    OrganizationsAPI.read.mockImplementation(getOrganizations);

    const wrapper = mountWithContexts(
      <Project setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 6
    );
    expect(tabs.at(3).text()).toEqual('Notifications');
    done();
  });

  test('notifications tab hidden with reduced permissions', async done => {
    ProjectsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    OrganizationsAPI.read.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    const wrapper = mountWithContexts(
      <Project setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 5
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    done();
  });

  test('schedules tab shown for scm based projects.', async done => {
    ProjectsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    OrganizationsAPI.read.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    const wrapper = mountWithContexts(
      <Project setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 5
    );
    expect(tabs.at(4).text()).toEqual('Schedules');
    done();
  });

  test('schedules tab hidden for manual projects.', async done => {
    const manualDetails = Object.assign(mockDetails, { scm_type: '' });
    ProjectsAPI.readDetail.mockResolvedValue({ data: manualDetails });
    OrganizationsAPI.read.mockResolvedValue({
      count: 0,
      next: null,
      previous: null,
      data: { results: [] },
    });

    const wrapper = mountWithContexts(
      <Project setBreadcrumb={() => {}} me={mockMe} />
    );
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 4
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Schedules'));
    done();
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/projects/1/foobar'],
    });
    const wrapper = mountWithContexts(
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
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
