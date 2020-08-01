import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  WorkflowJobTemplatesAPI,
  OrganizationsAPI,
  LabelsAPI,
} from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import WorkflowJobTemplateEdit from './WorkflowJobTemplateEdit';

jest.mock('../../../api/models/WorkflowJobTemplates');
jest.mock('../../../api/models/Labels');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/Inventories');

const mockTemplate = {
  id: 6,
  name: 'Foo',
  description: 'Foo description',
  summary_fields: {
    inventory: { id: 1, name: 'Inventory 1' },
    organization: { id: 1, name: 'Organization 1' },
    labels: {
      results: [
        { name: 'Label 1', id: 1 },
        { name: 'Label 2', id: 2 },
      ],
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
        results: [
          { name: 'Label 1', id: 1 },
          { name: 'Label 2', id: 2 },
          { name: 'Label 3', id: 3 },
        ],
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
    act(() => {
      wrapper.find('input#wfjt-name').simulate('change', {
        target: { value: 'Alex', name: 'name' },
      });
      wrapper.find('input#wfjt-description').simulate('change', {
        target: { value: 'Apollo and Athena', name: 'description' },
      });
      wrapper.find('input#wfjt-description').simulate('change', {
        target: { value: 'master', name: 'scm_branch' },
      });
      wrapper.find('input#wfjt-description').simulate('change', {
        target: { value: '5000', name: 'limit' },
      });
      wrapper
        .find('LabelSelect')
        .find('SelectToggle')
        .simulate('click');
    });

    wrapper.update();

    act(() => {
      wrapper
        .find('SelectOption')
        .find('button[aria-label="Label 3"]')
        .prop('onClick')();
    });

    wrapper.update();

    act(() =>
      wrapper
        .find('SelectOption')
        .find('button[aria-label="Label 1"]')
        .prop('onClick')()
    );

    wrapper.update();

    await act(async () => {
      wrapper.find('WorkflowJobTemplateForm').invoke('handleSubmit')();
    });

    expect(WorkflowJobTemplatesAPI.update).toHaveBeenCalledWith(6, {
      name: 'Alex',
      description: 'Apollo and Athena',
      inventory: 1,
      organization: 1,
      scm_branch: 'master',
      limit: '5000',
      extra_vars: '---',
      webhook_credential: null,
      webhook_url: '',
      webhook_service: '',
      allow_simultaneous: false,
      ask_inventory_on_launch: false,
      ask_limit_on_launch: false,
      ask_scm_branch_on_launch: false,
      ask_variables_on_launch: false,
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
          results: [
            { name: 'Label 1', id: 1 },
            { name: 'Label 2', id: 2 },
          ],
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
