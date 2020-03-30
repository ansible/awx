import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import WorkflowJobTemplate from './WorkflowJobTemplate';
import { sleep } from '@testUtils/testUtils';
import {
  WorkflowJobTemplatesAPI,
  CredentialsAPI,
  OrganizationsAPI,
} from '@api';

jest.mock('@api/models/WorkflowJobTemplates');
jest.mock('@api/models/Credentials');
jest.mock('@api/models/Organizations');

describe('<WorkflowJobTemplate/>', () => {
  const mockMe = {
    is_super_user: true,
    is_system_auditor: false,
  };
  let wrapper;
  let history;
  beforeAll(() => {
    WorkflowJobTemplatesAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        name: 'Foo',
        description: 'Bar',
        created: '2015-07-07T17:21:26.429745Z',
        modified: '2019-08-11T19:47:37.980466Z',
        extra_vars: '',
        summary_fields: {
          webhook_credential: { id: 1234567, name: 'Foo Webhook Credential' },
          created_by: { id: 1, username: 'Athena' },
          modified_by: { id: 1, username: 'Apollo' },
          recent_jobs: [
            { id: 1, status: 'run' },
            { id: 2, status: 'run' },
            { id: 3, status: 'run' },
          ],
          labels: {
            results: [
              { name: 'Label 1', id: 1 },
              { name: 'Label 2', id: 2 },
              { name: 'Label 3', id: 3 },
            ],
          },
        },
        related: {
          webhook_key: '/api/v2/workflow_job_templates/57/webhook_key/',
        },
      },
    });
    WorkflowJobTemplatesAPI.readWebhookKey.mockResolvedValue({
      data: { webhook_key: 'WebHook Key' },
    });
    CredentialsAPI.readDetail.mockResolvedValue({
      data: {
        summary_fields: {
          credential_type: { name: 'Github Personal Access Token', id: 1 },
        },
      },
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [{ id: 1, name: 'Org Foo' }] },
    });
  });
  beforeEach(() => {
    history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/details'],
    });
    act(() => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/workflow_job_template/:id/details"
          component={() => (
            <WorkflowJobTemplate setBreadcrumb={() => {}} me={mockMe} />
          )}
        />,
        {
          context: {
            router: {
              history,
            },
          },
        }
      );
    });
  });

  test('calls api to get workflow job template data', async () => {
    expect(wrapper.find('WorkflowJobTemplate').length).toBe(1);
    expect(WorkflowJobTemplatesAPI.readDetail).toBeCalledWith('1');
    wrapper.update();
    await sleep(0);
    expect(WorkflowJobTemplatesAPI.readWebhookKey).toBeCalledWith('1');
    expect(CredentialsAPI.readDetail).toBeCalledWith(1234567);
    expect(OrganizationsAPI.read).toBeCalledWith({
      page_size: 1,
      role_level: 'notification_admin_role',
    });
  });

  test('renders proper tabs', async () => {
    const tabs = [
      'Details',
      'Access',
      'Notifications',
      'Schedules',
      'Visualizer',
      'Completed Jobs',
      'Survey',
    ];
    waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper.update();
    wrapper.find('TabContainer').forEach(tc => {
      tabs.forEach(t => expect(tc.prop(`aria-label=[${t}]`)));
    });
  });

  test('Does not render Notifications tab', async () => {
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [] },
    });
    const tabs = [
      'Details',
      'Access',
      'Schedules',
      'Visualizer',
      'Completed Jobs',
      'Survey',
    ];
    waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper.update();
    wrapper.find('TabContainer').forEach(tc => {
      tabs.forEach(t => expect(tc.prop(`aria-label=[${t}]`)));
    });
  });
});
