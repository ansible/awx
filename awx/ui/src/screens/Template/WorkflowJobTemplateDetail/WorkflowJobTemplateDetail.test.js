import React from 'react';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';

import { WorkflowJobTemplateNodesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowJobTemplateDetail from './WorkflowJobTemplateDetail';

jest.mock('../../../api');

describe('<WorkflowJobTemplateDetail/>', () => {
  let wrapper;
  let history;
  const template = {
    id: 1,
    name: 'WFJT Template',
    description: 'Yo, it is a wfjt template!',
    type: 'workflow_job_template',
    extra_vars: '1: 2',
    created: '2015-07-07T17:21:26.429745Z',
    modified: '2019-08-11T19:47:37.980466Z',
    related: { webhook_receiver: '/api/v2/workflow_job_templates/45/github/' },
    summary_fields: {
      created_by: { id: 1, username: 'Athena' },
      modified_by: { id: 1, username: 'Apollo' },
      organization: { id: 1, name: 'Org' },
      inventory: { kind: 'Foo', id: 1, name: 'Bar' },
      labels: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
      },
      recent_jobs: [
        { id: 1, status: 'run' },
        { id: 2, status: 'run' },
        { id: 3, status: 'run' },
      ],
      webhook_credential: { id: '1', name: 'Credential', kind: 'machine' },
      user_capabilities: { edit: true, delete: true },
    },
    webhook_service: 'Github',
    webhook_key: 'Foo webhook key',
    scm_branch: 'main',
    limit: 'servers',
  };

  beforeEach(async () => {
    WorkflowJobTemplateNodesAPI.read.mockResolvedValue({ data: { count: 0 } });
    history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/templates/workflow_job_template/:id/details"
          component={() => (
            <WorkflowJobTemplateDetail
              template={template}
              hasContentLoading={false}
              onSetContentLoading={() => {}}
            />
          )}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  path: '/templates/workflow_job_template/1/details',
                  url: '/templates/workflow_job_template/1/details',
                },
              },
            },
          },
        }
      );
    });
  });

  test('renders successfully', () => {
    expect(wrapper.find(WorkflowJobTemplateDetail).length).toBe(1);
  });

  test('expect detail fields to render properly', () => {
    const renderedValues = [
      {
        element: 'UserDateDetail[label="Created"]',
        prop: 'date',
        value: '2015-07-07T17:21:26.429745Z',
      },
      {
        element: 'UserDateDetail[label="Modified"]',
        prop: 'date',
        value: '2019-08-11T19:47:37.980466Z',
      },
      {
        element: 'Detail[label="Webhook URL"]',
        prop: 'value',
        value: 'http://localhost/api/v2/workflow_job_templates/45/github/',
      },
      {
        element: 'Detail[label="Source Control Branch"]',
        prop: 'value',
        value: 'main',
      },
      {
        element: 'Detail[label="Limit"]',
        prop: 'value',
        value: 'servers',
      },
      {
        element: "Detail[label='Webhook Service']",
        prop: 'value',
        value: 'Github',
      },
      {
        element: 'Detail[label="Webhook Key"]',
        prop: 'value',
        value: 'Foo webhook key',
      },
      {
        element: 'Detail[label="Name"]',
        value: 'WFJT Template',
        prop: 'value',
      },
      {
        element: 'Detail[label="Description"]',
        prop: 'value',
        value: 'Yo, it is a wfjt template!',
      },
      {
        element: 'Detail[label="Job Type"]',
        prop: 'value',
        value: 'Workflow Job Template',
      },
    ];

    const organization = wrapper
      .find('Detail[label="Organization"]')
      .find('.pf-c-label__content');
    const inventory = wrapper.find('Detail[label="Inventory"]').find('a');
    const labels = wrapper
      .find('Detail[label="Labels"]')
      .find('Chip[component="div"]');
    const sparkline = wrapper.find('Sparkline Link');

    expect(organization.text()).toBe('Org');
    expect(inventory.text()).toEqual('Bar');
    expect(labels.length).toBe(3);
    expect(sparkline.length).toBe(3);

    const assertValue = (value) => {
      expect(wrapper.find(`${value.element}`).prop(`${value.prop}`)).toEqual(
        `${value.value}`
      );
    };

    renderedValues.map((value) => assertValue(value));
  });

  test('should have proper number of delete detail requests', async () => {
    expect(
      wrapper.find('DeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(1);
  });

  test('link out resource have the correct url', () => {
    const inventory = wrapper.find('Detail[label="Inventory"]').find('Link');
    const organization = wrapper
      .find('Detail[label="Organization"]')
      .find('Link');
    expect(inventory.prop('to')).toEqual('/inventories/inventory/1/details');
    expect(organization.prop('to')).toEqual('/organizations/1/details');
  });

  test('should not load Activity', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplateDetail
          template={{
            ...template,
            summary_fields: {
              ...template.summary_fields,
              recent_jobs: [],
            },
          }}
          hasContentLoading={false}
          onSetContentLoading={() => {}}
        />
      );
    });
    const activity_detail = wrapper.find(`Detail[label="Activity"]`).at(0);
    expect(activity_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load Labels', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowJobTemplateDetail
          template={{
            ...template,
            summary_fields: {
              ...template.summary_fields,
              labels: {
                results: [],
              },
            },
          }}
          hasContentLoading={false}
          onSetContentLoading={() => {}}
        />
      );
    });
    const labels_detail = wrapper.find(`Detail[label="Labels"]`).at(0);
    expect(labels_detail.prop('isEmpty')).toEqual(true);
  });
});
