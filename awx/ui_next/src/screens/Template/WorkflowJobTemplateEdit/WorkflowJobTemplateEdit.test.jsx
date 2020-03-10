import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { WorkflowJobTemplatesAPI, OrganizationsAPI, LabelsAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { createMemoryHistory } from 'history';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';

jest.mock('@api/models/WorkflowJobTemplates');
jest.mock('@api/models/Labels');
jest.mock('@api/models/Organizations');
jest.mock('@api/models/Inventories');

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
    LabelsAPI.read.mockResolvedValue({
      data: {
        results: [{ name: 'Label 1', id: 1 }, { name: 'Label 2', id: 2 }],
      },
    });
    OrganizationsAPI.read.mockResolvedValue({ results: [{ id: 1 }] });

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
    jest.clearAllMocks();
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
        inventory: 1,
        organization: 1,
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
      inventory: 1,
      organization: 1,
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

  test('handleCancel navigates the user to the /templates', () => {
    act(() => {
      wrapper.find('WorkflowJobTemplateForm').invoke('handleCancel')();
    });
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/6/details'
    );
  });

  test('throwing error renders FormSubmitError component', async () => {
    const error = {
      response: {
        config: {
          method: 'patch',
          url: '/api/v2/workflow_job_templates/',
        },
        data: { detail: 'An error occurred' },
      },
    };
    WorkflowJobTemplatesAPI.update.mockRejectedValue(error);
    await act(async () => {
      wrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalled();
    wrapper.update();
    expect(wrapper.find('WorkflowJobTemplateForm').prop('submitError')).toEqual(
      error
    );
  });

  test('throwing error prevents form submission', async () => {
    const templateWithoutOrg = {
      id: 6,
      name: 'Foo',
      description: 'Foo description',
      summary_fields: {
        inventory: { id: 1, name: 'Inventory 1' },
        labels: {
          results: [{ name: 'Label 1', id: 1 }, { name: 'Label 2', id: 2 }],
        },
      },
      scm_branch: 'devel',
      limit: '5000',
      variables: '---',
    };

    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <WorkflowJobTemplateEdit template={templateWithoutOrg} />,
        {
          context: {
            router: {
              history,
            },
          },
        }
      );
    });
    OrganizationsAPI.read.mockRejectedValue({
      response: {
        config: {
          method: 'get',
          url: '/api/v2/organizations/',
        },
        data: { detail: 'An error occurred' },
      },
    });

    WorkflowJobTemplatesAPI.update.mockResolvedValue();

    await act(async () => {
      await newWrapper.find('Button[aria-label="Save"]').simulate('click');
    });
    expect(newWrapper.find('WorkflowJobTemplateForm').length).toBe(1);
    expect(OrganizationsAPI.read).toBeCalled();
    expect(WorkflowJobTemplatesAPI.update).not.toBeCalled();
    expect(history.location.pathname).toBe(
      '/templates/workflow_job_template/6/edit'
    );
  });
});
