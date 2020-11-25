import React from 'react';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { WorkflowJobTemplatesAPI, OrganizationsAPI } from '../../api';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import WorkflowJobTemplate from './WorkflowJobTemplate';
import mockWorkflowJobTemplateData from './shared/data.workflow_job_template.json';

jest.mock('../../api/models/WorkflowJobTemplates');
jest.mock('../../api/models/Organizations');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};
describe('<WorkflowJobTemplate />', () => {
  let wrapper;
  beforeEach(() => {
    WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({
      data: mockWorkflowJobTemplateData,
    });
    WorkflowJobTemplatesAPI.readWorkflowJobTemplateOptions.mockResolvedValue({
      data: {
        actions: { PUT: true },
      },
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
    WorkflowJobTemplatesAPI.readWebhookKey.mockResolvedValue({
      data: {
        webhook_key: 'key',
      },
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('initially renders succesfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />
      );
    });
  });
  test('When component mounts API is called and the response is put in state', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    expect(WorkflowJobTemplatesAPI.readDetail).toBeCalled();
    expect(OrganizationsAPI.read).toBeCalled();
  });
  test('notifications tab shown for admins', async done => {
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />
      );
    });

    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 8
    );
    expect(tabs.at(3).text()).toEqual('Notifications');
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

    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    const tabs = await waitForElement(
      wrapper,
      '.pf-c-tabs__item',
      el => el.length === 7
    );
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    done();
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/foobar'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/templates/workflow_job_template/1/foobar',
                  path: '/templates/workflow_job_template/1/foobar',
                },
              },
            },
          },
        }
      );
    });

    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
  test('should call to get webhook key', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/templates/workflow_job_template/1/foobar',
                  path: '/templates/workflow_job_template/1/foobar',
                },
              },
            },
          },
        }
      );
    });
    expect(WorkflowJobTemplatesAPI.readWebhookKey).toHaveBeenCalled();
  });
  test('should not call to get webhook key', async () => {
    WorkflowJobTemplatesAPI.readWorkflowJobTemplateOptions.mockResolvedValueOnce(
      {
        data: {
          actions: {},
        },
      }
    );

    const history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/templates/workflow_job_template/1/foobar',
                  path: '/templates/workflow_job_template/1/foobar',
                },
              },
            },
          },
        }
      );
    });
    expect(WorkflowJobTemplatesAPI.readWebhookKey).not.toHaveBeenCalled();
  });
});
