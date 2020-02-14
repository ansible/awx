import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { WorkflowJobTemplatesAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';

import WorkflowJobTemplateAdd from './WorkflowJobTemplateAdd';

jest.mock('@api');

describe('<WorkflowJobTemplateAdd/>', () => {
  let wrapper;
  let history;
  beforeEach(async () => {
    WorkflowJobTemplatesAPI.create.mockResolvedValue({ data: { id: 1 } });
    await act(async () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/workflow_job_template/add'],
      });
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
  afterEach(async () => {
    wrapper.unmount();
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
    const error = new Error('oops');
    WorkflowJobTemplatesAPI.create.mockImplementation(() =>
      Promise.reject(error)
    );
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').prop('handleSubmit')({
        id: 6,
        name: 'Alex',
        description: 'Apollo and Athena',
        inventory: { id: 1, name: 'Inventory 1' },
        organization: 2,
        scm_branch: 'master',
        limit: '5000',
        variables: '---',
      });
    });
    wrapper.update();
    expect(WorkflowJobTemplatesAPI.create).toBeCalled();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });
});
