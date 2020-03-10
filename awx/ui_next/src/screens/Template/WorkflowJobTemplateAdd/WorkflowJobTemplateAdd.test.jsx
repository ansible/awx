import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { WorkflowJobTemplatesAPI, OrganizationsAPI, LabelsAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';

import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

jest.mock('@api/models/WorkflowJobTemplates');
jest.mock('@api/models/Organizations');
jest.mock('@api/models/Labels');
jest.mock('@api/models/Inventories');

describe('<WorkflowJobTemplateAdd/>', () => {
  let wrapper;
  let history;
  beforeEach(async () => {
    WorkflowJobTemplatesAPI.create.mockResolvedValue({ data: { id: 1 } });
    OrganizationsAPI.read.mockResolvedValue({ results: [{ id: 1 }] });
    LabelsAPI.read.mockResolvedValue({
      data: {
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
      },
    });

    await act(async () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/workflow_job_template/add'],
      });
      await act(async () => {
        wrapper = mountWithContexts(
          <Route
            path="/templates/workflow_job_template/add"
            component={() => <WorkflowJobTemplateAdd />}
          />,
          {
            context: {
              router: {
                history,
                route: {
                  location: history.location,
                },
              },
            },
          }
        );
      });
    });
  });
  afterEach(async () => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });

  test('calls workflowJobTemplatesAPI with correct information on submit', async () => {
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').invoke('handleSubmit')({
        name: 'Alex',
        labels: [{ name: 'Foo', id: 1 }, { name: 'bar', id: 2 }],
        organizationId: 1,
      });
    });
    expect(WorkflowJobTemplatesAPI.create).toHaveBeenCalledWith({
      name: 'Alex',
    });
    expect(WorkflowJobTemplatesAPI.associateLabel).toHaveBeenCalledTimes(2);
  });

  test('handleCancel navigates the user to the /templates', async () => {
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').invoke('handleCancel')();
    });
    expect(history.location.pathname).toBe('/templates');
  });

  test('throwing error renders FormSubmitError component', async () => {
    const error = {
      response: {
        config: {
          method: 'post',
          url: '/api/v2/workflow_job_templates/',
        },
        data: { detail: 'An error occurred' },
      },
    };

    WorkflowJobTemplatesAPI.create.mockRejectedValue(error);
    await act(async () => {
      wrapper.find('WorkflowJobTemplateForm').invoke('handleSubmit')({
        name: 'Foo',
      });
    });
    expect(WorkflowJobTemplatesAPI.create).toHaveBeenCalled();
    wrapper.update();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });

  test('throwing error prevents navigation away from form', async () => {
    OrganizationsAPI.read.mockRejectedValue({
      response: {
        config: {
          method: 'get',
          url: '/api/v2/organizations/',
        },
        data: 'An error occurred',
      },
    });
    WorkflowJobTemplatesAPI.update.mockResolvedValue();

    await act(async () => {
      await wrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(wrapper.find('WorkflowJobTemplateForm').length).toBe(1);
    expect(OrganizationsAPI.read).toBeCalled();
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/add'
    );
  });
});
