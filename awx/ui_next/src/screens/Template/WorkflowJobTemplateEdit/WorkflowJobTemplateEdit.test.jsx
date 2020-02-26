import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { WorkflowJobTemplatesAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';

jest.mock('@api');
const mockTemplate = {
  id: 6,
  name: 'Foo',
  description: 'Foo description',
  summary_fields: {
    inventory: { id: 1, name: 'Inventory 1' },
    organization: { id: 1, name: 'Organization 1' },
    labels: {
      results: [{ name: 'Label 1', id: 1 }, { name: 'Label 2', id: 2 }],
    },
  },
  scm_branch: 'devel',
  limit: '5000',
  variables: '---',
};
describe('<WorkflowJobTemplateEdit/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    await act(async () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/workflow_job_template/6/edit'],
      });
      wrapper = mountWithContexts(
        <Route
          path="/templates/workflow_job_template/:id/edit"
          component={() => <WorkflowJobTemplateEdit template={mockTemplate} />}
        />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { id: 6 } },
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

  test('renders successfully', () => {
    expect(wrapper.find('WorkflowJobTemplateEdit').length).toBe(1);
  });

  test('api is called to properly to save the updated template.', async () => {
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').invoke('handleSubmit')({
        id: 6,
        name: 'Alex',
        description: 'Apollo and Athena',
        inventory: { id: 1, name: 'Inventory 1' },
        organization: 2,
        labels: [{ name: 'Label 2', id: 2 }, { name: 'Generated Label' }],
        scm_branch: 'master',
        limit: '5000',
        variables: '---',
      });
    });

    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalledWith(6, {
      id: 6,
      name: 'Alex',
      description: 'Apollo and Athena',
      inventory: { id: 1, name: 'Inventory 1' },
      organization: 2,
      scm_branch: 'master',
      limit: '5000',
      variables: '---',
    });
    wrapper.update();
    await expect(WorkflowJobTemplatesAPI.disassociateLabel).toBeCalledWith(6, {
      name: 'Label 1',
      id: 1,
    });
    wrapper.update();

    await expect(WorkflowJobTemplatesAPI.associateLabel).toBeCalledTimes(1);
  });

  test('handleCancel navigates the user to the /templates', async () => {
    await act(async () => {
      await wrapper.find('WorkflowJobTemplateForm').invoke('handleCancel')();
    });
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/6/details'
    );
  });

  test('throwing error renders FormSubmitError component', async () => {
    const error = new Error('oops');
    WorkflowJobTemplatesAPI.update.mockImplementation(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('WorkflowJobTemplateForm').prop('handleSubmit')({
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
    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalled();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });
});
