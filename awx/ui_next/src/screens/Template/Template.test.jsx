import React from 'react';
import { createMemoryHistory } from 'history';
import { JobTemplatesAPI, OrganizationsAPI } from '@api';
import { act } from 'react-dom/test-utils';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import Template from './Template';
import mockJobTemplateData from './shared/data.job_template.json';

jest.mock('@api/models/JobTemplates');
jest.mock('@api/models/Organizations');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};
describe('<Template />', () => {
  beforeEach(() => {
    JobTemplatesAPI.readDetail.mockResolvedValue({
      data: mockJobTemplateData,
    });

    OrganizationsAPI.read.mockResolvedValue({
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
          },
        ],
      },
    });
  });
  test('initially renders succesfully', async () => {
    await act(async () => {
      mountWithContexts(<Template setBreadcrumb={() => {}} me={mockMe} />);
    });
  });
  test('When component mounts API is called and the response is put in state', async () => {
    await act(async () => {
      mountWithContexts(<Template setBreadcrumb={() => {}} me={mockMe} />);
    });
    expect(JobTemplatesAPI.readDetail).toBeCalled();
    expect(OrganizationsAPI.read).toBeCalled();
  });
  test('notifications tab shown for admins', async done => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Template setBreadcrumb={() => {}} me={mockMe} />
      );
    });

    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 6
    );
    expect(tabs.at(2).text()).toEqual('Notifications');
    done();
  });
  test('notifications tab hidden with reduced permissions', async done => {
    OrganizationsAPI.read.mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Template setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 5
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    done();
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/foobar'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Template setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/templates/job_template/1/foobar',
                  path: '/templates/job_template/1/foobar',
                },
              },
            },
          },
        }
      );
    });

    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
